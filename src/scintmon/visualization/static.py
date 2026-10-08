"""Renderização independente de navegador para PNG/SVG dos gráficos Plotly."""
from io import BytesIO
import numpy as np
import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
from scintmon.visualization.charts import COLORS


def export_figure(figure, format="png"):
    if format not in ("png", "svg"):
        raise ValueError("Formato deve ser png ou svg")
    polar = any(trace.type == "scatterpolar" for trace in figure.data)
    axis_refs = sorted(set(getattr(t, "yaxis", None) or "y" for t in figure.data))
    fig, axes = plt.subplots(len(axis_refs) if not polar else 1, 1,
                             figsize=(14 if polar else 11, max(8 if polar else 6, 3 * len(axis_refs))),
                             subplot_kw={"projection": "polar"} if polar else {}, squeeze=False)
    mapping = dict(zip(axis_refs, axes[:, 0]))
    first = axes[0, 0]
    if polar:
        first.set_theta_zero_location("N")
        first.set_theta_direction(-1)
        first.set_ylim(0, 90)
        first.set_yticks([0, 30, 60, 80, 90], labels=["90°", "60°", "30°", "10°", "0°"])
    bar_counts = {}
    for trace in figure.data:
        if trace.type == "bar":
            ref = getattr(trace, "yaxis", None) or "y"
            bar_counts[ref] = bar_counts.get(ref, 0) + 1
    bar_index = {}
    for index, trace in enumerate(figure.data):
        ax = first if polar else mapping[getattr(trace, "yaxis", None) or "y"]
        color = COLORS[index % len(COLORS)]
        line_color = getattr(getattr(trace, "line", None), "color", None)
        marker_color = getattr(getattr(trace, "marker", None), "color", None)
        if isinstance(line_color, str):
            color = line_color
        elif isinstance(marker_color, str):
            color = marker_color
        name = trace.name or ""
        if trace.type == "scatterpolar":
            theta, radius = np.radians(list(trace.theta)), list(trace.r)
            if "lines" in (trace.mode or ""):
                ax.plot(theta, radius, label=name,
                        color="#086baf" if name == "Elevação 30°" else color,
                        linestyle="--" if name == "Elevação 30°" else "-", linewidth=1)
            else:
                points = ax.scatter(theta, radius, c=list(trace.marker.color), cmap="viridis", s=18)
                fig.colorbar(points, ax=ax, label="S4 (adimensional)", pad=.12)
        elif trace.type == "heatmap":
            values = np.asarray(trace.z, dtype=float)
            if values.size:
                image = ax.imshow(values, origin="lower", aspect="auto", cmap="viridis")
                ax.set_xticks(range(len(trace.x)), labels=list(trace.x))
                ax.set_yticks(range(len(trace.y)), labels=list(trace.y))
                fig.colorbar(image, ax=ax, label="S4 (adimensional)")
        elif trace.type == "box":
            if len(trace.y):
                ax.boxplot(list(trace.y), positions=[index + 1], widths=.5)
                ax.set_xticks(range(1, index + 2), labels=[t.name for t in figure.data[:index + 1]])
        elif trace.type == "bar":
            ref = getattr(trace, "yaxis", None) or "y"
            count = bar_counts[ref]
            offset = bar_index.get(ref, 0)
            bar_index[ref] = offset + 1
            x = np.arange(len(trace.x)) + (offset - (count - 1) / 2) * .8 / count
            bars = ax.bar(x, list(trace.y), width=.8 / count, label=name, color=color)
            ax.set_xticks(range(len(trace.x)), labels=list(trace.x))
            if trace.text is not None:
                ax.bar_label(bars, labels=[f"N={v}" for v in trace.text], fontsize=8)
        else:
            x, y = list(trace.x), list(trace.y)
            if x and isinstance(x[0], str) and "T" in x[0]:
                from datetime import datetime
                x = [datetime.fromisoformat(v) for v in x]
            if "lines" in (trace.mode or ""):
                ax.plot(x, y, label=name, color=color, linewidth=1, marker=".")
            else:
                ax.scatter(x, y, label=name, color=color, s=12)
    for ref, ax in mapping.items():
        if polar:
            break
        suffix = ref[1:]
        xlayout = getattr(figure.layout, "xaxis" + suffix, None)
        ylayout = getattr(figure.layout, "yaxis" + suffix, None)
        ax.set_xlabel(xlayout.title.text or "Horário" if xlayout else "Horário")
        ax.set_ylabel(ylayout.title.text or "S4" if ylayout else "S4")
        if ylayout and ylayout.range:
            ax.set_ylim(*ylayout.range)
        for shape in figure.layout.shapes or []:
            if shape.type == "line" and shape.y0 == shape.y1:
                ax.axhline(shape.y0, linestyle="--", color="#647786", linewidth=1)
            if shape.type == "rect":
                ax.axvspan(shape.x0, shape.x1, color="#08a1c2", alpha=.1)
        ax.grid(alpha=.15)
        if ax.get_legend_handles_labels()[0]:
            handles, labels = ax.get_legend_handles_labels()
            unique = dict(zip(labels, handles))
            ax.legend(unique.values(), unique.keys(), fontsize=7, loc="best")
        ax.tick_params(axis="x", labelrotation=25)
    if polar:
        # Legenda à esquerda e escala de cor à direita: superfícies
        # distintas evitam sobreposição em comparação de várias noites.
        fig.legend(*first.get_legend_handles_labels(), fontsize=7, loc="upper left",
                   bbox_to_anchor=(.01, .88))
    fig.suptitle(figure.layout.title.text, fontsize=13)
    annotations = [a.text.replace("<br>", " · ") for a in figure.layout.annotations or [] if a.xref == "paper" and a.y < 0]
    import textwrap
    fig.text(.02, .01, "\n".join(textwrap.wrap(" · ".join(annotations), 150)), fontsize=7)
    if polar:
        fig.subplots_adjust(left=.2, right=.86, top=.86, bottom=.18)
    else:
        for annotation in figure.layout.annotations or []:
            if annotation.xref == "x" and annotation.yref == "y":
                x = annotation.x
                if isinstance(x, str) and "T" in x:
                    from datetime import datetime
                    x = datetime.fromisoformat(x)
                first.annotate(annotation.text, (x, annotation.y), xytext=(5, 8),
                               textcoords="offset points", fontsize=8)
        fig.tight_layout(rect=[0, .09, 1, .94])
    buffer = BytesIO()
    fig.savefig(buffer, format=format, dpi=160)
    plt.close(fig)
    return buffer.getvalue()
