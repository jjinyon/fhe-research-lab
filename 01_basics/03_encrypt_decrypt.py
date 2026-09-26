
from openfhe import *

# python 01_basics/03_encrypt_decrypt.py

def main():
    # 1. CKKS 파라미터 생성
    parameters = CCParamsCKKSRNS()
    parameters.SetMultiplicativeDepth(2)
    parameters.SetScalingModSize(50)
    parameters.SetBatchSize(8)

    # 2. CryptoContext 생성
    cc = GenCryptoContext(parameters)

    # 3. PKE 기능 활성화
    cc.Enable(PKESchemeFeature.PKE)

    # 4. 키 생성
    keys = cc.KeyGen()

    # 5. 암호화할 데이터
    values = [1.0, 2.0, 3.0, 4.0]

    # 6. 평문 인코딩
    plaintext = cc.MakeCKKSPackedPlaintext(values)

    # 7. 공개키로 암호화
    ciphertext = cc.Encrypt(keys.publicKey, plaintext)

    # 8. 비밀키로 복호화
    decrypted = cc.Decrypt(keys.secretKey, ciphertext)

    # 9. 복호화 결과의 출력 길이 설정
    decrypted.SetLength(len(values))

    decrypted_values = decrypted.GetRealPackedValue()
    
    # 10. 복호화된 실수 값 추출
    
    print("Original values:", values)
    print("Decrypted values:", decrypted_values)

    errors = [
        abs(original - recovered)
        for original, recovered in zip(values, decrypted_values)
    ]

    print("Absolute errors:", errors)
    print("Maximum error:", max(errors))

if __name__ == "__main__":
    main()