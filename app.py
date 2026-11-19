def divide(a, b):
    if b == 0:
        raise ValueError("Делитель не может быть нулём")
    return a / b

def main():
    try:
        result = divide(10, 0)
        print(f"Result: {result}")
    except ValueError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()