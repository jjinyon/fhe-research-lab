from openfhe import *

# python 01_basics/02_keygen.py

def main():

    # 1. CKKS 파라미터 생성
    parameters = CCParamsCKKSRNS()

    # 2. 암호 시스템 설정
    parameters.SetMultiplicativeDepth(2)
    parameters.SetScalingModSize(50)
    parameters.SetBatchSize(8)

    # 3. CryptoContext 생성
    cc = GenCryptoContext(parameters)

    # 4. PKE 기능 활성화
    cc.Enable(PKESchemeFeature.PKE)

    # 5. 키 생성
    keys = cc.KeyGen()

    # 6. 공개키와 비밀키 확인
    public_key = keys.publicKey # 평문을 암호화 할때 사용한다
    secret_key = keys.secretKey # 암호문을 복호화 할때 사용한다

    print("Key generation complete!")
    print("Public key generated:", public_key is not None)
    print("Secret key generated:", secret_key is not None)


if __name__ == "__main__":
    main()