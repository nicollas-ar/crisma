import os, secrets, json
from flask import Flask, request, jsonify, session, render_template_string
import psycopg

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
DB = os.environ.get("DATABASE_URL", "")
with open("questions.json", encoding="utf-8") as f:
    QUESTIONS = json.load(f)[:35]
LOOKUP = {q["id"]: q for q in QUESTIONS}

def connection():
    return psycopg.connect(DB) if DB else None

def init_db():
    if not DB: return
    with connection() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS scores (
          id BIGSERIAL PRIMARY KEY,
          name VARCHAR(32) NOT NULL,
          score INTEGER NOT NULL,
          waves INTEGER NOT NULL,
          created_at TIMESTAMPTZ DEFAULT NOW())""")
        c.execute("CREATE INDEX IF NOT EXISTS scores_top ON scores(score DESC, waves DESC)")
init_db()

@app.get("/")
def index():
    with open("index.html", encoding="utf-8") as f: return f.read()

@app.get("/saude")
def health():
    return jsonify(ok=True, database_configured=bool(DB))

@app.post("/api/start")
def start():
    name = str((request.get_json(silent=True) or {}).get("name","")).strip()[:32]
    if len(name)<2: return jsonify(error="Digite seu nome (mínimo 2 caracteres)."),400
    session.clear()
    session.update(name=name, wave=0, score=0, used=[], ended=False)
    return jsonify(ok=True, name=name)

@app.post("/api/question")
def question():
    if not session.get("name") or session.get("ended"): return jsonify(error="Inicie uma partida."),400
    if session.get("pending"): return jsonify(error="Responda primeiro."),409
    used=session.get("used",[])
    if len(used)>=len(QUESTIONS): used=[]
    q=secrets.choice([x for x in QUESTIONS if x["id"] not in used])
    used.append(q["id"])
    session["used"]=used
    session["pending"]=q["id"]
    return jsonify(question=q["question"], options=q["options"])

def save():
    if session.get("saved"): return
    session["saved"]=True
    if DB:
        with connection() as c:
            c.execute("INSERT INTO scores(name,score,waves) VALUES (%s,%s,%s)",
                      (session["name"],session["score"],session["wave"]))

@app.post("/api/answer")
def answer():
    if not session.get("name") or session.get("ended"): return jsonify(error="Partida encerrada."),400
    qid=session.get("pending")
    if not qid: return jsonify(error="Nenhuma pergunta pendente."),409
    q=LOOKUP[qid]
    try: choice=int((request.get_json(silent=True) or {}).get("choice",-1))
    except (ValueError,TypeError): choice=-1
    session.pop("pending",None)
    if choice==q["answer"]:
        session["wave"]=session["wave"]+1
        session["score"]=session["score"]+100
        return jsonify(correct=True,score=session["score"],waves=session["wave"])
    session["ended"]=True
    save()
    return jsonify(correct=False,answer=q["options"][q["answer"]],score=session["score"],waves=session["wave"])

@app.post("/api/end")
def end():
    if not session.get("name"): return jsonify(error="Sem partida."),400
    session["ended"]=True
    save()
    return jsonify(score=session["score"],waves=session["wave"])

@app.get("/api/ranking")
def ranking():
    if not DB: return jsonify([])
    with connection() as c:
        rows=c.execute("SELECT name,score,waves FROM scores ORDER BY score DESC,waves DESC,created_at ASC LIMIT 20").fetchall()
    return jsonify([dict(name=r[0],score=r[1],waves=r[2]) for r in rows])

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)))
