import pymupdf as pdf
from pathlib import Path
import regex as re
from transformers import AutoTokenizer, AutoModelForSequenceClassification,pipeline
import torch as torch
import nltk
from nltk.tokenize import sent_tokenize
import sys
import scipy.stats as stats
import numpy as np
import json

hawkish_labels =["withdrawal of accommodation", "raising interest rates", "tightening monetary policy"]
dovish_labels =["accommodative monetary policy", "lowering interest rates", "easing monetary policy"]
neutral_labels =["neutral monetary policy", "maintaining current rates", "unchanged monetary stance"]
ALL_LABELS = hawkish_labels + dovish_labels + neutral_labels        

MaxEntropy = np.log2(3)
EntropyThreshold = 0.90*MaxEntropy#placeholder for now will keep if it works properly

def Initialse_NLP():
    tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large-mnli", do_lower_case=True)
    model = AutoModelForSequenceClassification.from_pretrained("facebook/bart-large-mnli")
    if torch.cuda.is_available():
        device = torch.device("cuda")#gettinng hardware data taaki it runs everywhere
    elif torch.mps.is_available():
        device = torch.device("mps")
    else:
        device = torch.device("cpu")
    model.to(device)
    nltk.download("punkt")
    nltk.download('punkt_tab')
    model.eval()
    zero_shot_classifier = pipeline(
    "zero-shot-classification", 
    model=model, 
    tokenizer=tokenizer, 
    device=device
    )
    return(device, model,tokenizer, zero_shot_classifier)

def sentiment_score(outputs):
    retained_chunks = []
    for result in outputs:
        score_map = dict(zip(result["labels"], result["scores"]))
        
        # Averaging/summing the multiple labels into a single score for the logic below
        h_score = sum(score_map[l] for l in hawkish_labels)
        d_score = sum(score_map[l] for l in dovish_labels)
        n_score = sum(score_map[l] for l in neutral_labels)
        
        probs = np.array([h_score, d_score, n_score])
        chunk_entropy = stats.entropy(probs, base = 2)
        if chunk_entropy > EntropyThreshold:
            continue#discarding chunks the model is unsure of/ ambiguous chunks
        else:
            retained_chunks.append({"hawkish":h_score,"dovish":d_score,"neutral":n_score,"entropy":chunk_entropy})
    score = np.array([])
    neutrality_weights = np.array([])
    inverse_entropy_weights = np.array([])
    for dick in retained_chunks:
        score = np.append(score, (dick["hawkish"]-dick["dovish"]))
        neutrality_weights = np.append(neutrality_weights, (1-dick["neutral"]))#penalising highly neutral statements
        inverse_entropy_weights = np.append(inverse_entropy_weights, EntropyThreshold-dick["entropy"])#prioritising statements the model is sure off
    weights = neutrality_weights*inverse_entropy_weights
    sentiment_score = np.average(score, weights=weights)
    return sentiment_score

def main():
    device, model,tokenizer, zero_shot_classifier = Initialse_NLP()
    FINAL_SENTIMENT_SCORE = {}
    for file in Path("artifacts/").glob("*.pdf"):
        text = []
        file_name = file.name
        doc = pdf.open(file)
        count = 0
        for page in doc:
            count+=1
            if count == 1:
                rect = page.bound()
                top_margin = rect.height*0.22
                new_rect = pdf.Rect(rect.x0, rect.y0 + top_margin, rect.x1, rect.y1)
                #page.set_cropbox(new_rect)
                text.append(page.get_text(clip = new_rect))#removing header
            else:
                text.append(page.get_text())
        text = " ".join(text)
        text = re.sub(r"[\r\s]+", " ", text)
        text = re.sub(r"[\r\n]+", " ", text)
        text = sent_tokenize(text)
        outputs = zero_shot_classifier(text, candidate_labels = ALL_LABELS, multi_label=False,
                                            hypothesis_template="The sentiment of this monetary policy statement reflects {}.", batch_size = 32)
        sent_score = sentiment_score(outputs)
        FINAL_SENTIMENT_SCORE[file_name] = float(sent_score)
    print(FINAL_SENTIMENT_SCORE)
    with open("data/final_sentiment_score_1.json", "w") as file:
        json.dump(FINAL_SENTIMENT_SCORE, file, indent =  4)

if __name__ == "__main__":
    sys.exit(main())