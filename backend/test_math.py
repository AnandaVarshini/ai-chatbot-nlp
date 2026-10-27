"""Test math handler standalone."""
from app.math_handler import MathHandler

def main():
    mh = MathHandler()

    queries = [
        "2+2=",
        "10*5=",
        "100/4=",
        "sqrt(16)=",
        "sqrt(16)",
        "2+2",
        "what is 5 times 3",
        "(5+5)*2=",
    ]

    print("=" * 60)
    print("MATH HANDLER TEST")
    print("=" * 60)

    for q in queries:
        result = mh.solve(q)
        if result:
            print(f"  '{q}'  ->  {result}")
        else:
            print(f"  '{q}'  ->  (no match)")

if __name__ == "__main__":
    main()