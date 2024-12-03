import flet as ft
import json
import requests

# 気象庁APIのURL
FORECAST_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/{}.json"

def main(page: ft.Page):
    page.title = "天気予報アプリ"

    # 天気情報を表示するためのRow（初めは非表示）
    weather_details = ft.Row(
        [],
        visible=False,  # 初めは非表示
        wrap=True,  # 複数行に折り返す
    )

    # ローカルファイルから地域リストを取得
    def get_area_list():
        with open("/Users/satoreo/DS_prog_2/jma/areas.json", "r", encoding="utf-8") as f:
            area_data = json.load(f)
        return area_data

    # ターミナルにメッセージを出力する関数
    def print_message(message):
        print(message)

    # 天気情報を取得する関数
    def get_weather_data(area_code):
        url = FORECAST_URL.format(area_code)
        print_message(f"アクセスURL: {url}")
        try:
            response = requests.get(url)
            response.raise_for_status()  # HTTPエラーが発生した場合に例外を発生させる
            data_json = response.json()
            print_message(f"取得したデータ: {json.dumps(data_json, indent=2, ensure_ascii=False)}")  # デバッグ情報の出力
            return data_json
        except requests.exceptions.RequestException as e:
            error_message = f"HTTPリクエストエラー: {e}"
            print_message(error_message)
            return None
        except json.JSONDecodeError as e:
            error_message = f"JSONデコードエラー: {e}"
            print_message(error_message)
            return None

    # 七日間の天気情報を取得する関数
    def get_seven_days_weather(page, area_code):
        
        weather_data = get_weather_data(area_code)
        if weather_data is None:
            error_message = f"天気情報を取得できませんでした。地域コード: {area_code}"
            weather_details.controls = [ft.Text(error_message)]
            print_message(error_message)
            weather_details.visible = True
            page.update()
            return

        # 取得したデータをもとに天気情報を表示
        weather_cards = []
        for time_series in weather_data[0]['timeSeries']:
            time_defines = time_series['timeDefines'][:7]  # 最初の7つの日付を採用
            areas = time_series['areas']
            for area in areas:
                print_message(f"選択された地域コード: {area_code}")
                print_message(f"--- APIのエリアコード: {area['area']['code']} ---")
                if area['area']['code'] == area['area']['code'].startswith(area_code[:5]) or area_code:  # エリアコードが一致または五桁の一致
                    for i, time in enumerate(time_defines):
                        # `T`を除去した日付
                        forecast_date = time.split("T")[0]  # "T" を基準に分割し、日付部分だけを残す

                        # 各種情報を取得
                        temps_max = area.get('tempsMax', ['N/A'])
                        temps_min = area.get('tempsMin', ['N/A'])
                        pops = area.get('pops', ['N/A'])
                        weather_codes = area.get('weatherCodes', ['N/A'])

                        # インデックスが範囲内であることを確認
                        pop = pops[i] if i < len(pops) else 'N/A'
                        temp_max = temps_max[i] if i < len(temps_max) else 'N/A'
                        temp_min = temps_min[i] if i < len(temps_min) else 'N/A'
                        weather_code = weather_codes[i] if i < len(weather_codes) else 'N/A'

                        # 天気コードに基づくアイコンURLを生成
                        icon_url = f"https://www.jma.go.jp/bosai/forecast/img/{weather_code}.svg"

                        # 気温の表示形式を調整（青文字と赤文字）
                        weather_cards.append(
                            ft.Container(
                                content=ft.Column(
                                    controls=[
                                        ft.Text(f"日付: {forecast_date}"),
                                        ft.Image(src=icon_url, width=40, height=40),  # アイコン画像を表示
                                        ft.Text(f"天気コード: {weather_code}"),
                                        ft.Text(f"最低気温: {temp_min}°C", color=ft.colors.BLUE),
                                        ft.Text(f"最高気温: {temp_max}°C", color=ft.colors.RED),
                                        ft.Text(f"降水確率: {pop}%"),
                                    ]
                                ),
                                width=200,
                                height=250,
                                padding=10,
                                bgcolor=ft.colors.LIGHT_BLUE_50,
                                border_radius=10,
                                margin=5,
                            )
                        )
        if not weather_cards:
            error_message = "該当する天気情報がありません。"
            weather_details.controls = [ft.Text(error_message)]
        else:
            weather_details.controls = weather_cards

        weather_details.visible = True  # 天気情報を表示
        page.update()

    # 地域をリストとして表示
    def update_region_list(page):
        area_data = get_area_list()

        # 地域リストをリセット
        region_list.controls = []

        # 子地域を展開する関数
        def add_child_regions(parent_region, parent_code):
            child_controls = []
            if 'children' in parent_region:
                for child in parent_region['children']:
                    if child in area_data['offices']:
                        child_controls.append(
                            ft.ListTile(
                                title=ft.Text(area_data['offices'][child]['name']),
                                on_click=lambda e, area_code=child: get_seven_days_weather(page, area_code)
                            )
                        )
            return child_controls

        # 親地域を展開する関数
        def add_parent_region(region_data):
            for region_code, region in region_data.items():
                parent_region_name = region['name']
                # 子地域を追加
                child_regions = add_child_regions(region, region_code)
                if child_regions:
                    region_list.controls.append(
                        ft.ExpansionTile(
                            title=ft.Text(parent_region_name),
                            controls=child_regions
                        )
                    )

        # centersの地域を展開
        add_parent_region(area_data['centers'])

        region_list.visible = True  # 地域リストを表示
        page.update()

    # 地域リストを表示するためのColumn（初めは非表示）
    region_list = ft.Column(
        [],
        visible=False  # 初めは非表示
    )

    # 上部サイドバー（タイトル部分）
    top_bar = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.icons.WB_SUNNY, color=ft.colors.YELLOW),
                ft.Text("天気予報", size=20, color=ft.colors.WHITE),
                ft.Icon(ft.icons.MORE_VERT, color=ft.colors.WHITE),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=10,
        bgcolor=ft.colors.INDIGO,
        height=60,
    )

    # 地域選択の横幅を調整可能にするContainer
    regions_container = ft.Container(
        content=ft.ExpansionTile(
            title=ft.Text("地域を選択"),
            controls=[region_list]
        ),
        width=300,  # 横幅を調整可能
        padding=5,
    )

    # メインのレイアウト（上部にタイトル、左側に地域選択、右側に天気予報）
    content_column = ft.Row(
        controls=[
            ft.Column(
                controls=[
                    regions_container,  # 地域選択
                ],
                width=300,  # 横幅を調整可能
            ),
            ft.VerticalDivider(width=1),
            ft.Container(
                content=weather_details,  # 天気予報
                expand=True,
                padding=10,
            )
        ],
        expand=True,
    )

    # ページに追加
    page.add(
        ft.Column(
            controls=[
                top_bar,
                content_column,
            ],
            expand=True,
        )
    )

    # 最初に地域リストを更新
    update_region_list(page)

# Fletアプリを開始
ft.app(target=main)