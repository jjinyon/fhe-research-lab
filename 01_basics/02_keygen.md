## 9. 코드 실행 결과

```text
Key generation complete!
Public key generated: True
Secret key generated: True
```

공개키와 비밀키 객체가 정상적으로 생성된 것을 확인했다.

## 10. 핵심 API 정리

| API                            | 역할             |
| ------------------------------ | -------------- |
| `GenCryptoContext()`           | 암호 연산 환경 생성    |
| `Enable(PKESchemeFeature.PKE)` | 공개키 암호화 기능 활성화 |
| `KeyGen()`                     | 공개키와 비밀키 생성    |
| `keys.publicKey`               | 공개키 객체 가져오기    |
| `keys.secretKey`               | 비밀키 객체 가져오기    |

## 11. 이번 학습에서 이해한 점

공개키와 비밀키는 서로 다른 역할을 수행한다. 공개키로 암호화하고 비밀키로 복호화한다.

CKKS는 RLWE 계열의 어려운 문제에 기반하며, 키 생성 과정에서 공개키와 비밀키 사이에 수학적 관계가 형성된다.

## 12. 다음 단계

`03_encrypt_decrypt.py`에서 평문을 암호화하고 복호화하는 과정을 구현한다.

다음 단계에서는 `MakeCKKSPackedPlaintext()`, `Encrypt()`, `Decrypt()`의 역할과 CKKS 인코딩의 원리를 학습한다.
