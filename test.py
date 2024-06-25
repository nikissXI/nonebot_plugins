# from pydantic import BaseModel


# class Session(BaseModel):
#     chatCode: str = "0"
#     chatId: int = 0
#     price: int = 0


# data: dict[str, dict] = {
#     "111": {"chatCode": "abc", "chatId": 123, "price": 20},
#     "222": {"chatCode": "abc", "chatId": 123, "price": 20},
# }

# slist: dict[str, Session] = {}

# for uid, d in data.items():
#     slist[uid] = Session(**d)

# print(slist)
for i in range(5):
    print(i)
    break
else:
    print(111)
