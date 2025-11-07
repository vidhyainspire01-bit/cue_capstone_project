# utils/file_loader.py
import json
import re
from pathlib import Path
from uuid import uuid4
import nltk
nltk.download('punkt', quiet=True)
from nltk.tokenize import sent_tokenize
from docx import Document

CONTROL_RE = re.compile(r'[\x00-\x1f\x7f-\x9f]')

def clean_text(text: str) -> str:
    text = CONTROL_RE.sub(' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def read_docx(path: Path) -> str:
    doc = Document(path)
    paragraphs = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
    return '\n'.join(paragraphs)

def load_raw(path: Path):
    path = Path(path)
    suf = path.suffix.lower()
    if suf == '.docx':
        return read_docx(path)
    elif suf in ('.json',):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # txt/csv/other
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

def speaker_turns_from_transcript(text: str):
    """
    Expect transcripts with lines like: 'Rachel (CSM): text...'
    If no speaker labels present, treat whole text as one turn.
    """
    turns = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # heuristic: speaker label before first colon if short
        if ':' in line and len(line.split(':',1)[0]) < 60 and re.search(r'\w', line.split(':',1)[0]):
            speaker, body = line.split(':',1)
            turns.append({'speaker': speaker.strip(), 'text': clean_text(body.strip())})
        else:
            if turns:
                turns[-1]['text'] += ' ' + clean_text(line)
            else:
                turns.append({'speaker': None, 'text': clean_text(line)})
    return turns

def chunk_text_speaker_aware_from_text(text: str, chunk_size_words=700, overlap_words=150):
    turns = speaker_turns_from_transcript(text)
    chunks=[]
    cur=[]
    cur_words=0
    for t in turns:
        sents = sent_tokenize(t['text'])
        speaker_label = f"{t['speaker']}: " if t.get('speaker') else ""
        for s in sents:
            w = len(s.split())
            if cur_words + w > chunk_size_words and cur:
                chunks.append(' '.join(cur))
                # simple overlap: drop last N words from cur into new cur
                tail = ' '.join(' '.join(cur).split()[-overlap_words:]) if overlap_words>0 else ""
                cur = [tail] if tail else []
                cur_words = len(tail.split()) if tail else 0
            cur.append(speaker_label + s)
            cur_words += w
    if cur:
        chunks.append(' '.join(cur))
    return chunks

def emit_chunks_for_call_file(path: Path, doc_id=None, customer_id=None, date=None, chunk_size_words=700, overlap_words=150):
    raw = load_raw(path)
    # if raw is dict (json) and contains 'transcript_text', pull it
    if isinstance(raw, dict):
        txt = raw.get('transcript_text') or raw.get('transcript') or ' '.join([v for v in raw.values() if isinstance(v,str)]) 
        doc_id = doc_id or raw.get('call_id') or raw.get('doc_id')
        customer_id = customer_id or raw.get('customer_id')
        date = date or raw.get('date')
    else:
        txt = str(raw)
    txt = clean_text(txt)
    chunks = chunk_text_speaker_aware_from_text(txt, chunk_size_words=chunk_size_words, overlap_words=overlap_words)
    out=[]
    for i, c in enumerate(chunks):
        out.append({
            "chunk_id": str(uuid4()),
            "doc_id": doc_id or path.stem,
            "doc_type": "call",
            "customer_id": customer_id or path.parent.parent.name,  # try parent folder as customer
            "date": date or None,
            "chunk_index": i,
            "speaker": None,
            "tags": [],
            "text": c,
            "length_words": len(c.split()),
            "source_path": str(path)
        })
    return out
