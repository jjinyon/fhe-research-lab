from openfhe import *

'source ~/fhe-research-lab/.venv312/bin/activate'
' cd ~/fhe-research-lab '
' code . '
'python 01_basics/01_context.py'

def main():

    # CKKS 파라미터 생성
    parameters = CCParamsCKKSRNS()

    # 곱셈 깊이
    parameters.SetMultiplicativeDepth(2)

    # scaling factor의 크기
    parameters.SetScalingModSize(50)

    # SIMD slot 개수 설정
    parameters.SetBatchSize(8)

    # CryptoContext 생성
    cc = GenCryptoContext(parameters)

    print("CryptoContext created!")

    print("Ring dimension:",
          cc.GetRingDimension())


if __name__ == "__main__":
    main()