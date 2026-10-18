import matplotlib.pyplot as plt
from matplotlib.patches import Patch

fragile_color = "#e74c3c"
truck_edge_color = "#555555"


def _package_colors(state):
    cmap = plt.get_cmap("tab20")
    palette = [cmap(i) for i in range(cmap.N) if i not in (6, 7, 14, 15)]
    ids = sorted(p.package.id for p in state.placed)
    return {pid: palette[i % len(palette)] for i, pid in enumerate(ids)}


def _draw_truck(ax, truck):
    """Gambar kerangka (12 rusuk) peti kemas."""
    w, l, h = truck.w, truck.l, truck.h
    corners = [(0, 0), (w, 0), (w, l), (0, l)]
    for i in range(4):
        (x1, y1), (x2, y2) = corners[i], corners[(i + 1) % 4]
        for z in (0, h):  # rusuk alas & atap
            ax.plot([x1, x2], [y1, y2], [z, z], color=truck_edge_color, lw=1)
        ax.plot([x1, x1], [y1, y1], [0, h], color=truck_edge_color, lw=1)  # rusuk tegak


def _draw_packages(ax, state, colors, show_labels):
    for pp in state.inside_packages():
        x, y, z = pp.position
        dx, dy, dz = pp.dims()
        color = fragile_color if pp.package.is_fragile else colors[pp.package.id]
        ax.bar3d(x, y, z, dx, dy, dz, color=color, alpha=0.75,
                 edgecolor="black", linewidth=0.5, shade=True)
        if show_labels:
            ax.text(x + dx / 2, y + dy / 2, z + dz / 2, pp.package.id,
                    fontsize=6, ha="center", va="center")


def _summary_text(state, evaluator=None):
    truck = state.truck
    inside = state.inside_packages()
    outside = state.outside_packages()

    lines = [
        f"Value total : {state.total_value()}",
        f"Berat       : {state.total_weight()} / {truck.max_capacity}",
        f"Truk (WxLxH): {truck.w} x {truck.l} x {truck.h}",
        f"Di dalam    : {len(inside)} paket",
        f"Di luar     : {len(outside)} paket",
    ]
    if evaluator is not None:
        valid, reason = evaluator.validate(state)
        lines.append(f"Valid       : {valid} ({reason})")

    lines += ["", "Paket di luar:", f"{'id':<8}{'WxLxH':<8}{'val':>5}{'wt':>5}  F"]
    for pp in sorted(outside, key=lambda p: p.package.id):
        p = pp.package
        lines.append(
            f"{p.id:<8}{f'{p.w}x{p.l}x{p.h}':<8}{p.value:>5}{p.weight:>5}"
            f"  {'Y' if p.is_fragile else '-'}"
        )
    if not outside:
        lines.append("(tidak ada)")
    return "\n".join(lines)


def render_state(state, evaluator=None, title="", out_path=None, show=False, show_labels=True):
    truck = state.truck
    colors = _package_colors(state)

    fig = plt.figure(figsize=(13, 6.5))
    ax = fig.add_subplot(1, 2, 1, projection="3d")
    _draw_truck(ax, truck)
    _draw_packages(ax, state, colors, show_labels)

    ax.set_xlim(0, truck.w)
    ax.set_ylim(0, truck.l)
    ax.set_zlim(0, truck.h)
    ax.set_box_aspect((truck.w, truck.l, truck.h))  # biar proporsinya sesuai ukuran truk
    ax.set_xlabel("x (width)")
    ax.set_ylabel("y (length)")
    ax.set_zlabel("z (height)")
    ax.legend(
        handles=[Patch(color=fragile_color, label="fragile"),
                 Patch(color="#bbbbbb", label="non-fragile (warna per paket)")],
        loc="upper left", fontsize=8,
    )

    side = fig.add_subplot(1, 2, 2)
    side.axis("off")
    side.text(0, 1, _summary_text(state, evaluator), family="monospace",
              fontsize=9, va="top", ha="left", transform=side.transAxes)

    fig.suptitle(title or "State", fontsize=13)
    fig.tight_layout()

    if out_path:
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
    if show:
        plt.show()
    else:
        plt.close(fig)
    return fig
