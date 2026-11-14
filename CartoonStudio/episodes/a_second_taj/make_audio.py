"""Synthesize the six lines with Kokoro ONNX and time the 20-second scene."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
from urllib.request import urlopen
import numpy as np
import onnxruntime as ort
import soundfile as sf
from kokoro_onnx import Kokoro

ROOT = Path(__file__).resolve().parent
SAMPLE_RATE = 24000
FPS = 24
DURATION = 20
BASE_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
WEIGHTS = {
    "kokoro-v1.0.int8.onnx": "6e742170d309016e5891a994e1ce1559c702a2ccd0075e67ef7157974f6406cb",
    "voices-v1.0.bin": "bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d",
}

def model_file(name):
    path = Path(os.getenv("KOKORO_MODEL_DIR", ROOT / "models")) / name
    path.parent.mkdir(exist_ok=True, parents=True)
    if not path.is_file():
        import shutil
        tmp = path.with_suffix(path.suffix + ".part")
        with urlopen(BASE_URL + name, timeout=180) as response, tmp.open("wb") as out:
            shutil.copyfileobj(response, out)
        if hashlib.sha256(tmp.read_bytes()).hexdigest() != WEIGHTS[name]:
            tmp.unlink(missing_ok=True)
            raise ValueError(f"Downloaded checksum mismatch for {name}.")
        tmp.replace(path)
    if hashlib.sha256(path.read_bytes()).hexdigest() != WEIGHTS[name]:
        raise ValueError(f"Checksum mismatch for {path}.")
    return str(path)

def shot_sound(rate):
    # A short mechanical shutter: two clicks with slightly different springs.
    rng = np.random.default_rng(29)
    t = np.arange(int(.28*rate)) / rate
    y = np.zeros_like(t)
    for start, freq, level, decay in [(0,1650,.29,92),(.074,1030,.20,65),(.109,2400,.055,75)]:
        k=t>=start; x=t[k]-start
        noise=rng.uniform(-1,1,len(x))
        y[k]+=level*np.exp(-decay*x)*(np.sin(2*np.pi*freq*x)*.36+noise*.82)
    return y

def main():
    lines = json.loads((ROOT / "dialogue.json").read_text(encoding="utf-8"))
    if len(lines) != 6:
        raise ValueError("This six-shot scene expects six dialogue entries.")
    options = ort.SessionOptions()
    options.intra_op_num_threads = min(4, os.cpu_count() or 1)
    options.inter_op_num_threads = 1
    options.log_severity_level = 3
    session = ort.InferenceSession(model_file("kokoro-v1.0.int8.onnx"), sess_options=options, providers=["CPUExecutionProvider"])
    engine = Kokoro.from_session(session, model_file("voices-v1.0.bin"))
    clips = []
    for line in lines:
        wave, rate = engine.create(line["text"], voice=line["voice"], lang=line["language"], speed=line["speed"])
        if rate != SAMPLE_RATE:
            raise ValueError(f"Unexpected sample rate {rate}")
        wave = np.asarray(wave, dtype="float64")
        # Match the speakers' levels using the active portion of each recording.
        active = wave[np.abs(wave) > .008]
        if not len(active): raise ValueError(f"Silent line: {line['text']}")
        gain = min(.77 / np.max(np.abs(wave)), .116 / np.sqrt(np.mean(active ** 2)))
        clips.append(wave * gain)
    available = DURATION - 1.10 - .98 - sum(map(len, clips)) / SAMPLE_RATE
    if available < .65:
        raise ValueError("The lines leave too little reaction time. Shorten the dialogue or raise its Kokoro speed.")
    pauses = np.array([.52,.55,.68,.66,.79]); pauses *= available / sum(pauses)
    audio = np.zeros((SAMPLE_RATE * DURATION, 2))
    open_values = {k: np.zeros(FPS*DURATION) for k in ["Tara","Maya"]}
    timing = []
    start = 1.10
    for i,(line,wave) in enumerate(zip(lines, clips)):
        ix = round(start*SAMPLE_RATE)
        pan = (-.13 if line["speaker"] == "Tara" else .13)
        angle = (1+pan)*np.pi/4
        audio[ix:ix+len(wave)] += wave[:,None]*np.array([np.cos(angle),np.sin(angle)])[None,:]*1.30
        mono = np.zeros(SAMPLE_RATE*DURATION)
        mono[ix:ix+len(wave)] = wave
        energies=[]
        for frame in range(FPS*DURATION):
            center=int((frame+.50)/FPS*SAMPLE_RATE)
            block=mono[max(0,center-420):min(len(mono),center+420)]
            energies.append(np.sqrt(np.mean(block*block)) if len(block) else 0)
        vals=np.asarray(energies)
        strength=np.clip((vals-.004)/max(.035,np.percentile(vals[vals>.005],92)),0,1)**.65
        curve=np.convolve(strength,[.13,.75,.12],mode="same")
        open_values[line["speaker"]]=np.maximum(open_values[line["speaker"]],curve)
        end=(ix+len(wave))/SAMPLE_RATE
        timing.append({"speaker":line["speaker"],"start":round(ix/SAMPLE_RATE,4),"end":round(end,4),"text":line["text"]})
        start=end+(pauses[i] if i<len(pauses) else 0)
    # Quiet exterior room tone and a few distant birds, all synthesized.
    rng=np.random.default_rng(202)
    t=np.arange(len(audio))/SAMPLE_RATE
    dry=rng.normal(0,1,len(t))
    breeze=np.convolve(dry,np.ones(40)/40,mode="same")*.0065*(.72+.28*np.sin(t*.7))
    audio+=breeze[:,None]
    for start, f, side in [(0.22,2450,.75),(.44,2750,.75),(7.35,2900,.2),(12.85,2500,.75),(19.52,2350,.2)]:
        pos=round(start*SAMPLE_RATE); length=round(.16*SAMPLE_RATE); tt=np.arange(length)/SAMPLE_RATE
        bird=.011*np.sin(2*np.pi*(f*tt+270*tt*tt/.16))*np.sin(np.pi*tt/.16)**2
        audio[pos:pos+length]+=bird[:,None]*np.array([side,1-side])[None,:]
    shutter_time=19.34
    sound=shot_sound(SAMPLE_RATE); ix=round(shutter_time*SAMPLE_RATE)
    audio[ix:ix+len(sound)] += sound[:,None]*.65
    out=ROOT/"audio";out.mkdir(exist_ok=True)
    sf.write(out/"Conversation.wav",np.clip(audio,-.98,.98),SAMPLE_RATE,subtype="PCM_16")
    data={"fps":FPS,"duration":DURATION,"shutter":shutter_time,"lines":timing,
          "mouth":{k:np.round(v,3).tolist() for k,v in open_values.items()}}
    (out/"timing.json").write_text(json.dumps(data,indent=2),encoding="utf-8")
    for line in timing: print(f"{line['start']:5.2f}–{line['end']:5.2f}  {line['speaker']}  {line['text']}")
    print(session.get_providers()[0], "•", SAMPLE_RATE, "Hz •", DURATION, "seconds")

if __name__ == "__main__":
    main()
