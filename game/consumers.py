import json
import random
import time
from channels.generic.websocket import AsyncWebsocketConsumer

# MVP: RAM'de oda state'i (server kapanırsa sıfırlanır)
ROOMS = {}

# Şimdilik 3 il ile test (sonra 81'e genişleteceğiz)
PROVINCES = [
    {"id": "TR06", "name": "Ankara"},
    {"id": "TR34", "name": "Istanbul"},
    {"id": "TR35", "name": "Izmir"},
]

def pick_target():
    return random.choice(PROVINCES)

class RoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_code = self.scope["url_route"]["kwargs"]["room_code"]
        self.group_name = f"room_{self.room_code}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        if self.room_code not in ROOMS:
            ROOMS[self.room_code] = {
                "players": {},          # channel_name -> {name, score}
                "started": False,
                "ends_at": None,
                "current_target": None,
            }

        await self.send(text_data=json.dumps({
            "type": "hello",
            "room": self.room_code
        }))

    async def disconnect(self, close_code):
        room = ROOMS.get(self.room_code)
        if room and self.channel_name in room["players"]:
            del room["players"][self.channel_name]
            await self.broadcast_state()

        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data or "{}")
        t = data.get("type")
        room = ROOMS[self.room_code]

        if t == "join":
            name = (data.get("name") or "Player").strip()[:24]
            room["players"][self.channel_name] = {"name": name, "score": 0}
            await self.broadcast_state()
            return

        if t == "start":
            if not room["started"]:
                room["started"] = True
                room["ends_at"] = int(time.time()) + 60
                room["current_target"] = pick_target()

                await self.channel_layer.group_send(self.group_name, {
                    "type": "game_started",
                    "ends_at": room["ends_at"],
                    "current_target": room["current_target"],
                })
                await self.broadcast_state()
            return

        if t == "answer":
            if not room["started"]:
                return

            now = int(time.time())
            if room["ends_at"] and now >= room["ends_at"]:
                room["started"] = False
                await self.channel_layer.group_send(self.group_name, {"type": "game_ended"})
                await self.broadcast_state()
                return

            clicked_id = data.get("id")
            target = room["current_target"]
            if not target:
                return

            is_correct = (clicked_id == target["id"])
            if is_correct:
                room["players"][self.channel_name]["score"] += 10

            await self.channel_layer.group_send(self.group_name, {
                "type": "answer_result",
                "by": room["players"][self.channel_name]["name"],
                "clicked_id": clicked_id,
                "correct_id": target["id"],
                "correct_name": target["name"],
                "is_correct": is_correct,
                "scores": self.sorted_scores(room),
            })

            # yeni soru
            room["current_target"] = pick_target()
            await self.channel_layer.group_send(self.group_name, {
                "type": "new_question",
                "current_target": room["current_target"],
            })

            await self.broadcast_state()
            return

    def sorted_scores(self, room):
        items = list(room["players"].values())
        items.sort(key=lambda x: x["score"], reverse=True)
        return items

    async def broadcast_state(self):
        room = ROOMS[self.room_code]
        await self.channel_layer.group_send(self.group_name, {
            "type": "state_update",
            "started": room["started"],
            "ends_at": room["ends_at"],
            "current_target": room["current_target"],
            "scores": self.sorted_scores(room),
        })

    # ===== group handlers =====
    async def state_update(self, event):
        await self.send(text_data=json.dumps({
            "type": "state",
            "started": event["started"],
            "ends_at": event["ends_at"],
            "current_target": event["current_target"],
            "scores": event["scores"],
        }))

    async def game_started(self, event):
        await self.send(text_data=json.dumps({
            "type": "started",
            "ends_at": event["ends_at"],
            "current_target": event["current_target"],
        }))

    async def new_question(self, event):
        await self.send(text_data=json.dumps({
            "type": "question",
            "current_target": event["current_target"],
        }))

    async def answer_result(self, event):
        await self.send(text_data=json.dumps({
            "type": "result",
            "by": event["by"],
            "clicked_id": event["clicked_id"],
            "correct_id": event["correct_id"],
            "correct_name": event["correct_name"],
            "is_correct": event["is_correct"],
            "scores": event["scores"],
        }))

    async def game_ended(self, event):
        await self.send(text_data=json.dumps({"type": "ended"}))
