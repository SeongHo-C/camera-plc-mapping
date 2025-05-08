import json


def save_json(path, data):
    with open(path, 'w', encoding='utf-8-sig') as json_file:
        json.dump(data, json_file)

    print(f'{path} 저장 완료')


async def load_json(path, websocket):
    try:
        with open(path, 'r', encoding='utf-8-sig') as json_file:
            json_data = json.load(json_file)

        await websocket.send(json.dumps({
            'type': 'mapping',
            'data': json_data
        }))
    except Exception as e:
        print(f'JSON 파일 불러오기 실패: {e}')
