import { useEffect, useRef } from "react";
import Plotly from "plotly.js-dist-min";
import type { Data, Layout } from "plotly.js";

export function Plot({
  data,
  layout,
  label,
}: {
  data: Data[];
  layout?: Partial<Layout>;
  label: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const element = ref.current!;
    let ready = false;
    void Plotly.react(
      element,
      data,
      {
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        font: {
          family: "ui-monospace, SFMono-Regular, Consolas, monospace",
          color: "#9aabb9",
          size: 11,
        },
        margin: { l: 54, r: 24, t: 26, b: 50 },
        xaxis: {
          gridcolor: "#21303b",
          zerolinecolor: "#334550",
          title: { text: "Separation r/a" },
        },
        yaxis: {
          gridcolor: "#21303b",
          zerolinecolor: "#334550",
          title: { text: "Potential aV" },
        },
        legend: { orientation: "h", y: 1.2, x: 0 },
        autosize: true,
        ...layout,
      },
      {
        responsive: false,
        displaylogo: false,
        modeBarButtonsToRemove: ["lasso2d", "select2d"],
      },
    ).then(() => {
      ready = true;
    });
    const observer = new ResizeObserver(() => {
      if (
        ready &&
        element.isConnected &&
        element.getClientRects().length &&
        element.clientWidth > 0
      )
        void Promise.resolve(Plotly.Plots.resize(element)).catch(() => {
          /* A details panel may close before async resize. */
        });
    });
    observer.observe(element);
    return () => {
      ready = false;
      observer.disconnect();
      Plotly.purge(element);
    };
  }, [data, layout]);
  return <div className="plot" ref={ref} role="img" aria-label={label} />;
}
