# FHE Research Lab 작업 명령어 가이드

## 1. PC 재부팅 후

### WSL 실행

```bash
wsl
```

Windows에서 WSL Ubuntu를 실행합니다.

### 프로젝트 이동

```bash
cd ~/fhe-research-lab
```

연구 프로젝트 폴더로 이동합니다.

### VS Code 실행

```bash
code .
```

현재 WSL 프로젝트를 VS Code로 엽니다.

---

## 2. Python 환경

### 가상환경 활성화

```bash
source ~/fhe-research-lab/.venv312/bin/activate
```

OpenFHE 연구용 Python 환경을 활성화합니다.

### Python 위치 확인

```bash
which python
```

현재 사용 중인 Python을 확인합니다.

정상:

```text
/home/jinyong/fhe-research-lab/.venv312/bin/python
```

### OpenFHE 확인

```bash
python -c "from openfhe import *; print('OpenFHE OK')"
```

OpenFHE가 정상적으로 연결되었는지 확인합니다.

---

## 3. 코드 작성 및 실행

코드는 **VS Code에서 작성/수정**합니다.

### Python 코드 실행

```bash
python 파일경로.py
```

예:

```bash
python 01_ckks_basics/01_context.py
```

작성한 실험 코드를 실행합니다.

---

## 4. GitHub에 저장

### 변경사항 확인

```bash
git status
```

변경된 파일을 확인합니다.

### Git에 추가

```bash
git add .
```

변경된 파일을 Git에 추가합니다.

### Commit

```bash
git commit -m "변경 내용"
```

현재 작업 내용을 저장합니다.

예:

```bash
git commit -m "Add CKKS multiplication experiment"
```

### GitHub에 업로드

```bash
git push
```

Commit한 내용을 GitHub에 업로드합니다.

---

# ⭐ 매일 사용하는 핵심 명령어

PC 재부팅 후:

```bash
wsl
cd ~/fhe-research-lab
code .
source ~/fhe-research-lab/.venv312/bin/activate
```

연구 후:

```bash
git add .
git commit -m "변경 내용"
git push
```

**코드 작성/수정 → VS Code**

**코드 실행 → VS Code 터미널**

**연구 기록 저장 → GitHub**
