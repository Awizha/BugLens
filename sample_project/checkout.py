from discounts import discounted_price

def checkout_total(price):
    # apply a 20 % discount
    return discounted_price(price, 0.20)


if __name__ == "__main__":
    print(checkout_total(100))
    