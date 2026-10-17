import { jsxs as m, jsx as i } from "react/jsx-runtime";
import { createRoot as p } from "react-dom/client";
import { Pane as l, TableView as u } from "@plugboard/sdk";
function f({ artifact: n, dataset: o, agentTitle: e, onClose: t }) {
  const c = (o == null ? void 0 : o.rows) || [];
  return /* @__PURE__ */ m(l, { title: n.title, subtitle: `${e || "Starter"} · ${n.id} · ${c.length} rows`, onClose: typeof t == "function" ? t : void 0, children: [
    !o && /* @__PURE__ */ i("div", { style: { padding: "16px 20px", color: "var(--color-muted)", fontSize: 14 }, children: "Loading…" }),
    o && /* @__PURE__ */ i(u, { widget: { ...o, total_rows: c.length }, bare: !0 })
  ] });
}
const s = { StarterPane: f }, r = /* @__PURE__ */ new WeakMap();
function h(n, o) {
  const e = s[o.component];
  let t = r.get(n);
  t || (t = p(n), r.set(n, t)), t.render(e ? /* @__PURE__ */ i(e, { ...o }) : /* @__PURE__ */ m("div", { style: { padding: 16 }, children: [
    "Unknown component ",
    o.component
  ] }));
}
function v(n) {
  const o = r.get(n);
  o && (o.unmount(), r.delete(n));
}
export {
  h as mount,
  v as unmount
};
