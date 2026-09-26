# CKKS 이해

## 0. CKKS를 공부하는 이유

CKKS는 **실수와 복소수의 근사 연산을 지원하는 동형암호 방식**이다.

이번 학습에서는 CKKS를 두 단계로 나누어 이해한다.

```text
[기초]

CKKS가 무엇인가?
    ↓
Packing
    ↓
Encoding
    ↓
Scaling
    ↓
Encryption
    ↓
Decryption
    ↓
Approximation


[심화]

Polynomial Ring
    ↓
Canonical Embedding
    ↓
RLWE
    ↓
Noise
    ↓
Rescaling
    ↓
Modulus Chain
    ↓
Multiplicative Depth
    ↓
Bootstrapping
```

현재 `03_encrypt_decrypt.py`에서는 **기초 부분을 직접 코드로 확인**한다.

심화 부분은 현재 단계에서는 전체 구조를 이해하는 것을 목표로 하고, 이후 동형 연산을 공부하면서 하나씩 다시 자세히 다룬다.

---

# PART 1. CKKS 기초

## 1. CKKS란?

CKKS는 암호화된 상태에서 실수와 복소수에 대한 **근사적인 연산**을 수행할 수 있는 동형암호 방식이다.

일반적인 암호화에서는 데이터를 암호화하면 연산하기 어렵다.

```text
평문
 ↓
암호화
 ↓
암호문
```

암호문을 계산하려면 일반적으로 먼저 복호화해야 한다.

하지만 동형암호에서는

```text
평문 x
 ↓
Enc
 ↓
암호문 Enc(x)

평문 y
 ↓
Enc
 ↓
암호문 Enc(y)

Enc(x) + Enc(y)
 ↓
복호화
 ↓
x + y
```

와 같은 계산이 가능하다.

CKKS에서는 정확히

$$
Dec(Enc(x)+Enc(y))=x+y
$$

가 아니라,

$$
Dec(Enc(x)+Enc(y))\approx x+y
$$

가 된다.

CKKS는 **근사 동형암호**이기 때문이다.

---

# 2. CKKS의 전체 흐름

이번 `03_encrypt_decrypt.py`에서는 다음 과정을 수행한다.

```text
실수 벡터
[1.0, 2.0, 3.0, 4.0]
        ↓
Encoding
        ↓
CKKS Plaintext
        ↓
Encryption
        ↓
Ciphertext
        ↓
Decryption
        ↓
CKKS Plaintext
        ↓
Decoding
        ↓
[1.000..., 2.000..., 3.000..., 4.000...]
```

여기서 반드시 구분해야 하는 것이 있다.

### Encoding

데이터를 CKKS가 사용할 수 있는 형태로 변환한다.

### Encryption

CKKS 평문을 암호문으로 변환한다.

### Decryption

암호문을 다시 CKKS 평문으로 복원한다.

### Decoding

CKKS 평문에서 우리가 사용하는 실수 벡터를 복원한다.

---

# 3. Packing

CKKS의 중요한 특징 중 하나는 여러 데이터를 하나의 암호문에 넣을 수 있다는 것이다.

예를 들어

```python
values = [1.0, 2.0, 3.0, 4.0]
```

라는 데이터를 생각해 보자.

개념적으로 다음과 같이 볼 수 있다.

```text
Slot 0 → 1.0
Slot 1 → 2.0
Slot 2 → 3.0
Slot 3 → 4.0
```

따라서 각각의 값을 따로 암호화하는 대신 하나의 CKKS 암호문에 여러 값을 넣을 수 있다.

이 구조를 **packing**이라고 한다.

---

# 4. 왜 Packing이 중요한가?

Packing을 사용하면 하나의 동형 연산으로 여러 값에 동시에 연산할 수 있다.

예를 들어

$$
[1,2,3,4]+[10,20,30,40]
$$

을 수행하면

$$
[11,22,33,44]
$$

가 된다.

즉,

```text
[1,  2,  3,  4]
 +   +   +   +
[10,20,30,40]
 ↓   ↓   ↓   ↓
[11,22,33,44]
```

와 같은 SIMD 방식의 병렬 처리가 가능하다.

이러한 특징 때문에 CKKS는 머신러닝, 통계 계산, 벡터 연산 등에 적합하다.

---

# 5. Encoding

코드에서는 다음 부분이다.

```python
values = [1.0, 2.0, 3.0, 4.0]

plaintext = cc.MakeCKKSPackedPlaintext(values)
```

여기서 중요한 것은 `MakeCKKSPackedPlaintext()`가 **암호화 함수가 아니라는 것**이다.

실수 벡터를 CKKS가 사용할 수 있는 평문 표현으로 변환한다.

```text
[1.0, 2.0, 3.0, 4.0]
        ↓
CKKS Encoding
        ↓
CKKS Plaintext
```

따라서 다음 두 과정은 완전히 다르다.

```text
Encoding
데이터 표현 변환

Encryption
데이터 암호화
```

---

# 6. Encryption

코드:

```python
ciphertext = cc.Encrypt(keys.publicKey, plaintext)
```

여기서 실제 암호화가 수행된다.

```text
CKKS Plaintext
      +
Public Key
      ↓
   Encrypt
      ↓
Ciphertext
```

공개키를 이용해 암호화하기 때문에 공개키를 알고 있는 주체는 데이터를 암호화할 수 있다.

하지만 암호문을 복호화하려면 비밀키가 필요하다.

---

# 7. Decryption

코드:

```python
decrypted = cc.Decrypt(keys.secretKey, ciphertext)
```

암호문을 비밀키로 복호화한다.

개념적으로

$$
c=Enc(m)
$$

일 때

$$
Dec(c)\approx m
$$

을 얻는다.

복호화 결과는 아직 Python 리스트가 아니라 CKKS 평문이다.

---

# 8. Decoding

코드:

```python
decrypted.SetLength(len(values))

decrypted_values = decrypted.GetRealPackedValue()
```

`GetRealPackedValue()`를 통해 CKKS 평문에서 우리가 사용하는 실수 벡터를 추출한다.

전체 과정은 다음과 같다.

```text
Ciphertext
    ↓
Decrypt
    ↓
CKKS Plaintext
    ↓
Decode
    ↓
Python 실수 벡터
```

---

# 9. 왜 결과가 완전히 같지 않을 수 있는가?

CKKS의 핵심 특징이다.

복호화 결과가

```text
Original

[1.0, 2.0, 3.0, 4.0]
```

이고,

```text
Decrypted

[0.9999999998,
 2.0000000001,
 3.0000000002,
 3.9999999997]
```

처럼 나올 수 있다.

이는 CKKS가 **근사 연산을 목표로 하기 때문**이다.

따라서

$$
Dec(Enc(x))\approx x
$$

라고 표현한다.

---

# 10. Scaling

CKKS는 실수를 그대로 암호화하는 것이 아니라 내부적으로 스케일링을 사용한다.

개념적으로

$$
m\approx \lfloor \Delta x\rceil
$$

와 같이 생각할 수 있다.

여기서

* \(x\): 원래 값
* \(\Delta\): scaling factor
* \(m\): 스케일링된 값

이다.

예를 들어 단순화하여

$$
x=1.234
$$

이고

$$
\Delta=1000
$$

이라면

$$
1.234\times1000=1234
$$

가 된다.

실제 CKKS에서는 훨씬 복잡한 다항식 및 복소수 구조에서 스케일링이 수행된다.

---

# 11. `SetScalingModSize(50)`의 의미

코드:

```python
parameters.SetScalingModSize(50)
```

여기서 `50`은 **소수점 이하 50자리의 정확도**를 의미하지 않는다.

스케일링과 관련된 모듈러스 크기를 비트 단위로 설정하는 값이다.

따라서

```text
50
↓
50자리 정밀도
```

라고 이해하면 안 된다.

정확도는 scaling뿐만 아니라 여러 CKKS 파라미터와 연산 과정의 영향을 받는다.

---

# PART 2. CKKS 심화

## 12. Polynomial Ring

CKKS의 실제 암호 연산은 다항식 링을 기반으로 한다.

개념적으로

$$
R_q=\mathbb{Z}_q[X]/(X^N+1)
$$

와 같은 구조를 사용한다.

여기서

* \(N\): 링 차원
* \(q\): 모듈러스
* \(X\): 다항식 변수

이다.

예를 들어

$$
a_0+a_1X+a_2X^2+\cdots
$$

와 같은 다항식이 링의 원소가 된다.

우리가 사용하는 실수 벡터가 직접 이 형태로 존재하는 것은 아니다.

CKKS의 Encoding 과정을 통해 벡터가 다항식 링의 표현으로 연결된다.

---

# 13. Canonical Embedding

CKKS의 Encoding을 더 깊게 이해하려면 **Canonical Embedding**을 알아야 한다.

CKKS는 단순히

```text
[1,2,3,4]
↓
다항식 계수 [1,2,3,4]
```

처럼 변환하지 않는다.

대신 복소수 슬롯과 다항식 링 사이의 대응 관계를 사용한다.

개념적으로

$$
\text{Complex Slots}
\leftrightarrow
\text{Polynomial Ring}
$$

의 관계를 만든다.

따라서 CKKS의 Encoding은

```text
실수/복소수 벡터
        ↓
Canonical Embedding
        ↓
Polynomial
```

의 구조를 가진다.

이 부분은 이후 CKKS 수학을 깊게 공부할 때 중요하다.

---

# 14. RLWE

CKKS의 암호학적 보안은 RLWE 계열의 어려운 문제에 기반한다.

개념적인 형태를 단순화하면

$$
b=-as+e \pmod q
$$

와 같은 관계를 생각할 수 있다.

여기서

* \(a\): 공개되는 무작위 다항식
* \(s\): 비밀키
* \(e\): 작은 오차
* \(b\): 공개키 구성 요소
* \(q\): 모듈러스

이다.

작은 오차 \(e\)가 존재하기 때문에 공개된 정보만 가지고 \(s\)를 찾는 것이 어렵도록 설계된다.

실제 OpenFHE 구현은 이보다 복잡하며 RNS 등의 구조가 추가된다.

---

# 15. Noise

동형암호에서 Noise는 매우 중요한 개념이다.

개념적으로 암호문을

$$
Ciphertext
=
Message+Noise
$$

와 같이 생각할 수 있다.

Noise는 암호학적 보안을 위해 필요하다.

하지만 동형 연산에서는 동시에 문제가 된다.

예를 들어

$$
c_1=m_1+e_1
$$

$$
c_2=m_2+e_2
$$

라고 단순화하면

$$
c_1+c_2
=
m_1+m_2+(e_1+e_2)
$$

가 된다.

즉 연산 과정에서 Noise가 변화한다.

---

# 16. 곱셈에서 Noise가 더 중요해지는 이유

곱셈을 생각해 보자.

$$
c_1=m_1+e_1
$$

$$
c_2=m_2+e_2
$$

이면

$$
c_1c_2
=
m_1m_2
+
m_1e_2
+
m_2e_1
+
e_1e_2
$$

가 된다.

즉 단순히 Noise가 더해지는 것뿐 아니라 메시지와 Noise가 서로 곱해지는 항도 발생한다.

그래서 동형암호에서는 **곱셈 깊이**가 매우 중요하다.

---

# 17. Multiplicative Depth

코드:

```python
parameters.SetMultiplicativeDepth(2)
```

에서 설정했던 값이다.

곱셈 깊이는 단순히 곱셈의 개수가 아니다.

예를 들어

$$
(a\times b)\times(c\times d)
$$

는 총 3번의 곱셈을 수행하지만 곱셈 깊이는 2이다.

```text
Level 0

a   b   c   d
│   │   │   │
└─×─┘   └─×─┘
   │       │
   └───×───┘
       │
     Level 2
```

CKKS에서는 가능한 곱셈 깊이가 제한되기 때문에 회로 설계가 중요하다.

---

# 18. Modulus Chain

CKKS에서는 하나의 거대한 모듈러스만 사용하는 것이 아니라 여러 단계의 모듈러스를 사용하는 구조를 생각할 수 있다.

개념적으로

$$
Q=q_Lq_{L-1}\cdots q_1q_0
$$

와 같은 형태의 modulus chain을 사용한다.

곱셈과 rescaling을 수행하면서 일부 modulus가 제거된다.

```text
qL
 ↓
qL-1
 ↓
qL-2
 ↓
...
 ↓
q0
```

따라서 연산을 계속 수행하면 사용할 수 있는 modulus가 감소한다.

이것이 곱셈 깊이와 연결된다.

---

# 19. Rescaling

CKKS에서 곱셈을 수행하면 scaling factor가 커진다.

예를 들어

$$
\Delta m_1
$$

과

$$
\Delta m_2
$$

를 곱하면 대략

$$
\Delta^2m_1m_2
$$

와 같은 스케일을 갖게 된다.

즉 scaling factor가

$$
\Delta\rightarrow\Delta^2
$$

로 증가한다.

이 문제를 해결하기 위해 **Rescaling**을 사용한다.

개념적으로

$$
\frac{c}{q_i}
$$

와 같은 연산을 통해 scaling과 modulus를 함께 낮춘다고 생각할 수 있다.

```text
Multiplication
      ↓
Scale 증가
      ↓
Rescaling
      ↓
Scale 감소
      ↓
다음 연산
```

---

# 20. Noise와 Rescaling의 관계

Rescaling은 단순히 숫자의 크기를 줄이는 기능이 아니다.

CKKS에서

```text
Multiplication
      ↓
Scale 증가
      ↓
Noise 영향
      ↓
Rescaling
      ↓
Modulus 감소
```

라는 trade-off가 발생한다.

따라서 CKKS 파라미터를 설계할 때

* 정확도
* Noise
* Scale
* Modulus
* Multiplicative Depth
* 계산량

을 함께 고려해야 한다.

---

# 21. Bootstrapping

연산을 계속하면 modulus와 noise에 의해 더 이상 정확한 계산을 수행하기 어려워진다.

이를 해결하기 위한 방법 중 하나가 **Bootstrapping**이다.

개념적으로

```text
Ciphertext
    ↓
많은 연산
    ↓
Noise 증가
    ↓
계산 가능 범위 감소
    ↓
Bootstrapping
    ↓
새로운 계산 가능 상태
```

와 같이 이해할 수 있다.

Bootstrapping은 암호문을 다시 fresh한 상태에 가깝게 만들어 더 많은 연산을 수행할 수 있도록 한다.

CKKS에서 Bootstrapping은 매우 중요한 고급 주제이며, 이후 별도의 실험으로 다룬다.

---

# 22. 기초와 심화의 연결

지금까지의 내용을 하나의 흐름으로 연결하면 다음과 같다.

```text
[기초]

Vector
 ↓
Packing
 ↓
Encoding
 ↓
Scaling
 ↓
Encryption
 ↓
Ciphertext


[동형 연산]

Ciphertext
 ↓
Addition / Multiplication
 ↓
Noise 증가
 ↓
Scale 변화
 ↓
Rescaling


[심화]

Modulus Chain
 ↓
Multiplicative Depth
 ↓
계산 한계
 ↓
Bootstrapping
```

즉 CKKS를 공부할 때 각각의 개념을 독립적으로 외우는 것이 아니라 **하나의 계산 과정으로 연결해서 이해하는 것**이 중요하다.

---

# 23. 현재 단계에서 반드시 기억할 것

현재는 다음 7개만 확실하게 이해하면 된다.

### ① Packing

여러 값을 하나의 암호문에 넣는다.

### ② Encoding

실수/복소수 벡터를 CKKS 평문으로 변환한다.

### ③ Encryption

평문을 암호문으로 변환한다.

### ④ Decryption

암호문을 평문으로 복원한다.

### ⑤ Decoding

CKKS 평문을 실수/복소수 벡터로 복원한다.

### ⑥ Approximation

CKKS는 정확한 연산이 아니라 근사 연산을 수행한다.

### ⑦ Noise

암호화와 동형 연산 과정에서 오차가 존재하고 변화한다.

---

# 24. 전체 핵심 수식

현재 CKKS를 한 줄로 표현하면

$$
Decode(Decrypt(Enc(Encode(x))))
\approx x
$$

이다.

동형 연산까지 포함하면

$$
Decode
\left(
Decrypt
\left(
Eval
\left(
Enc(Encode(x))
\right)
\right)
\right)
\approx
Eval(x)
$$

이다.

이 수식이 CKKS를 이해하는 핵심적인 출발점이다.

---

# 25. 다음 학습

다음 단계에서는 실제로 암호문끼리 연산한다.

먼저 덧셈을 수행한다.

$$
Dec(EvalAdd(Enc(x),Enc(y)))
\approx x+y
$$

그 다음 곱셈을 수행한다.

$$
Dec(EvalMult(Enc(x),Enc(y)))
\approx x\times y
$$

특히 곱셈부터는

```text
Multiplication
      ↓
Scale 변화
      ↓
Noise 변화
      ↓
Rescaling
      ↓
Modulus Chain
```

이 등장하기 시작한다.

따라서 `03_encrypt_decrypt.py`에서는 **CKKS의 데이터 흐름**을 이해하고, 다음 실험부터는 **CKKS가 실제로 암호문에서 계산을 수행하는 과정**을 관찰한다.
