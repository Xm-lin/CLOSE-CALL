"""遊戲與畫圖工具共用的座標讀取規則；不需要額外套件。"""
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAP_DIR = ROOT / 'map'


def parse_points(text):
    text = text.lstrip('\ufeff').strip()
    if not text:
        raise ValueError('座標檔是空的')
    try:
        points = json.loads(re.sub(r',\s*]', ']', text))
    except json.JSONDecodeError:
        points = []
        for number, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            match = re.fullmatch(r'\s*\[?\s*(-?\d+(?:\.\d+)?)\s*[,\s]\s*(-?\d+(?:\.\d+)?)\s*\]?,?\s*', line)
            if not match:
                raise ValueError(f'第 {number} 行格式錯誤')
            points.append([float(match[1]), float(match[2])])
    if not isinstance(points, list) or any(
        not isinstance(p, list) or len(p) != 2 or
        any(type(v) not in (int, float) or not math.isfinite(v) for v in p)
        for p in points
    ):
        raise ValueError('每個座標必須是兩個有限數字：[x, y]')
    if len(points) > 1 and points[0] == points[-1]:
        points = points[:-1]
    if not 4 <= len(points) <= 2000:
        raise ValueError('請提供 4～2000 個座標')
    for i, b in enumerate(points):
        a, c = points[i - 1], points[(i + 1) % len(points)]
        ux, uy = b[0] - a[0], b[1] - a[1]
        vx, vy = c[0] - b[0], c[1] - b[1]
        if math.hypot(vx, vy) < .01:
            raise ValueError(f'第 {i + 1} 點與下一點重複')
        if abs(math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)) > math.pi - .001:
            raise ValueError(f'第 {i + 1} 點直接折返，請補上彎道節點')
    return points


def read_points(path):
    return parse_points(Path(path).read_text(encoding='utf-8-sig'))


def list_maps():
    MAP_DIR.mkdir(exist_ok=True)
    return [{'file': p.name, 'name': re.sub(r'^\d+[_ -]', '', p.stem)}
            for p in sorted(MAP_DIR.iterdir(), key=lambda p: p.name.casefold())
            if p.is_file() and p.suffix.lower() == '.txt']


def build_catalog():
    """更新純靜態網站的 maps.js 清單與離線備份，不啟動伺服器。"""
    records, bundled = list_maps(), []
    for record in records:
        try:
            bundled.append({**record, 'points': read_points(MAP_DIR / record['file'])})
        except ValueError as error:
            print(f"略過 {record['file']}：{error}")
    (ROOT / 'maps.js').write_text('// 由 draw.py --update-list 產生；網站平常直接讀取 map/*.txt。\nwindow.BUILTIN_MAPS = ' + json.dumps(bundled, ensure_ascii=False) + ';\n', encoding='utf-8')
    return records

def place_labels(fig, ax, annotations):
    """以實際螢幕文字框找空位；密集點用引線指回原座標。"""
    renderer = fig.canvas.get_renderer()
    occupied = []
    for ann in annotations:
        found = False
        for radius in [10, 22, 36, 52, 72, 96, 124, 156, 192]:
            for i in range(16):
                angle = i * math.pi / 8
                ann.set_position((radius * math.cos(angle), radius * math.sin(angle)))
                ann.update_positions(renderer)
                ann.update_bbox_position_size(renderer)
                box = ann.get_bbox_patch().get_window_extent(renderer).expanded(1.13, 1.2)
                if not ax.bbox.contains(box.x0, box.y0) or not ax.bbox.contains(box.x1, box.y1):
                    continue
                if not any(box.overlaps(other) for other in occupied):
                    occupied.append(box)
                    found = True
                    break
            if found:
                break
        ann.set_visible(found)
    return occupied


def plot_map(path, label_mode='index'):
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    candidates = ['Microsoft JhengHei', 'Noto Sans CJK TC', 'PingFang TC', 'WenQuanYi Zen Hei', 'SimHei']
    available = {font.name for font in font_manager.fontManager.ttflist}
    cjk_font = next((name for name in candidates if name in available), None)
    if cjk_font:
        plt.rcParams['font.sans-serif'] = [cjk_font, 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    points = read_points(path)
    fig = plt.figure(figsize=(13, 9))
    grid = fig.add_gridspec(1, 2, width_ratios=[3.5, 1.6])
    ax, table_ax = fig.add_subplot(grid[0]), fig.add_subplot(grid[1])
    closed_points = points + [points[0]]
    x, y = zip(*closed_points)
    ax.plot(x, y, '-o', color='#386747', markersize=4, linewidth=1.5)
    ax.scatter(*points[0], color='#d95230', s=65, zorder=4, label='Start')
    ax.invert_yaxis()
    ax.set_aspect('equal', adjustable='box')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_title('Track coordinates')
    ax.grid(True, alpha=.25)
    ax.legend(loc='upper right')
    ax.margins(.17)
    table_ax.set_axis_off()
    # 完整座標放在獨立欄位；圖上只放短編號，避免座標擠成一團。
    table_ax.text(0, 1, 'POINT / (X, Y)', transform=table_ax.transAxes, fontsize=10, weight='bold')
    if len(points) <= 80:
        columns = 1 if len(points) <= 40 else 2
        rows = math.ceil(len(points) / columns)
        for i, (px, py) in enumerate(points):
            col, row = divmod(i, rows)
            table_ax.text(col / columns, .96 - row * .91 / max(rows - 1, 1),
                          f'{i:02d}  ({px:g}, {py:g})', transform=table_ax.transAxes,
                          fontsize=8.5 if columns == 1 else 7, family='monospace')
    else:
        table_ax.text(0, .94, f'{len(points)} points\nHover near a point\nto inspect its coordinates.',
                      transform=table_ax.transAxes, fontsize=10, va='top')
    caption = Path(path).stem if cjk_font else 'Map ' + Path(path).stem.split('_')[0]
    fig.text(.04, .025, caption, fontsize=10, color='#555555')
    info = fig.text(.04, .006, 'Hover over a point to see coordinates.', fontsize=9)
    annotations = []
    if label_mode != 'none':
        stride = max(1, math.ceil(len(points) / 80))
        for i in range(0, len(points), stride):
            px, py = points[i]
            text = str(i) if label_mode == 'index' else f'{i}: ({px:g}, {py:g})'
            annotations.append(ax.annotate(text, (px, py), xytext=(8, 8), textcoords='offset points',
                                           ha='center', va='center', fontsize=8,
                                           bbox=dict(facecolor='white', edgecolor='none', alpha=.9, pad=1),
                                           arrowprops=dict(arrowstyle='-', color='#92978a', lw=.6)))
    fig.subplots_adjust(left=.065, right=.98, top=.94, bottom=.10, wspace=.16)
    fig.canvas.draw()
    place_labels(fig, ax, annotations)

    def hover(event):
        if event.inaxes is not ax or event.x is None:
            return
        xy = ax.transData.transform(points)
        distances = [(pos[0] - event.x) ** 2 + (pos[1] - event.y) ** 2 for pos in xy]
        index = min(range(len(points)), key=distances.__getitem__)
        if distances[index] < 144:
            px, py = points[index]
            text = f'Point {index}: ({px:g}, {py:g})'
            if info.get_text() != text:
                info.set_text(text)
                fig.canvas.draw_idle()

    def resize(event):
        # 重新計算文字框，視窗縮放後仍盡量避免相互覆蓋。
        for ann in annotations:
            ann.set_visible(True)
        place_labels(fig, ax, annotations)
        fig.canvas.draw_idle()

    fig.canvas.mpl_connect('motion_notify_event', hover)
    fig.canvas.mpl_connect('resize_event', resize)
    return fig, ax, annotations


def main():
    import argparse
    parser = argparse.ArgumentParser(description='讀取 map/*.txt 畫圖；編號避讓，完整座標獨立列出。')
    parser.add_argument('file', nargs='?', help='座標檔路徑；未指定時從 map 選擇')
    parser.add_argument('--all', action='store_true', help='畫出全部地圖')
    parser.add_argument('--output', type=Path, help='PNG 輸出資料夾')
    parser.add_argument('--labels', choices=['index', 'coords', 'none'], default='index')
    parser.add_argument('--no-show', action='store_true', help='只輸出圖片')
    parser.add_argument('--update-list', action='store_true', help='只更新 maps.js，不畫圖')
    args = parser.parse_args()
    records = build_catalog()
    if args.update_list:
        print(f'已更新 maps.js，共 {len(records)} 張地圖。直接上傳即可，不需要伺服器。')
        return
    try:
        import matplotlib
        if args.no_show:
            matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        parser.exit(1, '請先安裝：python -m pip install matplotlib\n')
    if args.all:
        paths = [MAP_DIR / r['file'] for r in records]
    elif args.file:
        path = Path(args.file)
        paths = [path if path.is_file() else ROOT / path]
    elif records:
        for i, item in enumerate(records, 1):
            print(f"{i}. {item['name']}")
        try:
            number = input('選擇地圖編號（Enter = 1）：').strip() or '1'
            index = int(number) - 1
            if not 0 <= index < len(records):
                raise ValueError
        except (ValueError, EOFError):
            parser.exit(1, '請輸入有效的地圖編號。\n')
        paths = [MAP_DIR / records[index]['file']]
    else:
        parser.exit(1, 'map 資料夾沒有 txt，請指定座標檔路徑。\n')
    output = args.output
    if args.no_show and output is None:
        output = ROOT / 'plots'
    if output:
        output.mkdir(parents=True, exist_ok=True)
    for path in paths:
        try:
            fig, _, _ = plot_map(path, args.labels)
        except (ValueError, OSError) as error:
            parser.exit(1, f'{path.name}：{error}\n')
        if output:
            fig.savefig(output / f'{path.stem}.png', dpi=160)
            print(f'已輸出 {path.stem}.png')
        if args.no_show:
            plt.close(fig)
    if not args.no_show:
        plt.show()


if __name__ == '__main__':
    main()
