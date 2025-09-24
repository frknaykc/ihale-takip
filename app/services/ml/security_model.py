import os
import joblib
import numpy as np
from sentence_transformers import SentenceTransformer, util

SIM_THR = float(os.getenv("SEC_SIM_THR", "0.70"))
PROB_THR = float(os.getenv("SEC_PROB_THR", "0.85"))
EMB_NAME = os.getenv("SEC_EMB_NAME", "paraphrase-multilingual-MiniLM-L12-v2")

_EMB = None
_CAT = None
_CLF = None
_MODEL_VERSION = None


def _load_embedder():
    global _EMB
    if _EMB is None:
        _EMB = SentenceTransformer(EMB_NAME)
    return _EMB


def _load_category_embedding():
    global _CAT
    if _CAT is None:
        texts = [
            "siber güvenlik hizmetleri SOC SIEM SOAR XDR NDR EDR IDS IPS malware tehdit istihbaratı zafiyet yönetimi",
            "cyber security operations incident response endpoint detection firewall sandbox network detection response",
        ]
        emb = _load_embedder().encode(texts, convert_to_tensor=True).mean(dim=0)
        _CAT = emb
    return _CAT


def _load_classifier():
    global _CLF, _MODEL_VERSION
    if _CLF is None:
        path = os.getenv("SEC_CLF_PATH", "sec_clf.joblib")
        if os.path.exists(path):
            obj = joblib.load(path)
            _CLF = obj["clf"]
            _MODEL_VERSION = obj.get("version", "clf_v1")
        else:
            _CLF = None
            _MODEL_VERSION = f"emb_only:{EMB_NAME}"
    return _CLF, _MODEL_VERSION


def score_text(text: str):
    emb = _load_embedder().encode(text, convert_to_tensor=True)
    cat = _load_category_embedding()
    sim = float(util.cos_sim(emb, cat).item())

    clf, ver = _load_classifier()
    if clf is not None:
        prob = float(clf.predict_proba(emb.cpu().numpy().reshape(1, -1))[0, 1])
    else:
        prob = sim

    accept = (sim >= SIM_THR) and (prob >= PROB_THR)
    return {
        "accept": bool(accept),
        "prob": prob,
        "sim": sim,
        "model_version": ver,
    }

