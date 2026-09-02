import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from temperans import TrajectoryStore


def load_trajectories(db, user_id, trajectory_id):
    store = TrajectoryStore(db)

    trace = store.trace(
        user_id=user_id,
        trajectory_id=trajectory_id,
        conversation_id="temperans_ui",
    )

    analyses = trace.analyze_trajectories()

    data = []

    for thread_id, analysis in analyses.items():
        timeline = trace.timeline(thread_id=thread_id)

        first_human = next(
            (
                e for e in timeline
                if e["actor_type"] == "human"
            ),
            None,
        )

        title = (
            first_human["text"][:55]
            if first_human
            else thread_id
        )

        data.append({
            "thread_id": thread_id,
            "title": title,
            "state": analysis.state,
            "providers": analysis.providers,
            "conversations": analysis.conversation_count,
            "human_turns": analysis.human_turns,
            "agent_turns": analysis.agent_turns,
            "evidence": analysis.evidence,
            "timeline": timeline,
        })

    store.close()

    return data


def page(data):
    payload = json.dumps(data)

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Temperans</title>

<style>
body {{
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: #0d0f12;
    color: #f4f5f7;
}}

header {{
    padding: 20px 28px;
    border-bottom: 1px solid #272b32;
    display: flex;
    justify-content: space-between;
}}

.brand {{
    font-size: 20px;
    font-weight: 650;
}}

.follow {{
    color: #72d69a;
}}

.layout {{
    display: grid;
    grid-template-columns: 330px 1fr;
    min-height: calc(100vh - 65px);
}}

aside {{
    border-right: 1px solid #272b32;
    padding: 22px;
}}

.label {{
    color: #89919d;
    font-size: 12px;
    margin-bottom: 14px;
}}

.item {{
    display: block;
    width: 100%;
    text-align: left;
    padding: 14px;
    margin-bottom: 8px;
    border-radius: 10px;
    border: 1px solid transparent;
    background: transparent;
    color: inherit;
    cursor: pointer;
}}

.item:hover,
.item.active {{
    background: #171a20;
    border-color: #303640;
}}

.item-title {{
    font-weight: 600;
    line-height: 1.35;
}}

.meta {{
    margin-top: 7px;
    color: #929ba8;
    font-size: 13px;
    line-height: 1.5;
}}

main {{
    padding: 36px 44px;
    max-width: 950px;
}}

h1 {{
    margin: 0;
    font-size: 27px;
}}

.state {{
    display: inline-block;
    margin-top: 12px;
    padding: 5px 9px;
    border: 1px solid #343a44;
    border-radius: 20px;
    font-size: 12px;
    text-transform: uppercase;
}}

.stats {{
    display: flex;
    gap: 36px;
    margin: 28px 0 34px;
}}

.number {{
    font-size: 22px;
    font-weight: 650;
}}

.stat-label {{
    color: #89919d;
    font-size: 12px;
}}

.section {{
    color: #89919d;
    font-size: 12px;
    text-transform: uppercase;
    margin: 28px 0 16px;
}}

.event {{
    border-left: 2px solid #343a44;
    padding: 0 0 25px 20px;
}}

.source {{
    color: #89919d;
    font-size: 12px;
}}

.text {{
    margin-top: 6px;
    line-height: 1.55;
}}

.evidence {{
    padding: 16px;
    background: #15181d;
    border: 1px solid #292e36;
    border-radius: 10px;
    line-height: 1.7;
    color: #b4bbc5;
}}

@media(max-width:760px) {{
    .layout {{
        grid-template-columns: 1fr;
    }}

    aside {{
        border-right: none;
        border-bottom: 1px solid #272b32;
    }}

    main {{
        padding: 24px;
    }}
}}
</style>
</head>

<body>

<header>
<div class="brand">temperans</div>
<div class="follow">● FOLLOWING</div>
</header>

<div class="layout">

<aside>
<div class="label">TRAJECTORIES</div>
<div id="list"></div>
</aside>

<main id="detail">
Select a trajectory.
</main>

</div>

<script>
const trajectories = {payload};

const list = document.getElementById("list");
const detail = document.getElementById("detail");

function escapeHTML(value) {{
    const node = document.createElement("div");
    node.textContent = value == null ? "" : String(value);
    return node.innerHTML;
}}

function providers(t) {{
    return t.providers.length
        ? t.providers.join(" → ")
        : "unknown";
}}

function render(t, index) {{
    document.querySelectorAll(".item")
        .forEach(x => x.classList.remove("active"));

    document.querySelector(
        '[data-index="' + index + '"]'
    )?.classList.add("active");

    const events = t.timeline.map(e => {{
        const provider =
            e.metadata?.provider ||
            e.actor_id ||
            e.actor_type;

        return `
        <div class="event">
            <div class="source">
                ${{escapeHTML(provider)}}
                · ${{escapeHTML(e.actor_type)}}
                · ${{escapeHTML(e.conversation_id)}}
            </div>

            <div class="text">
                ${{escapeHTML(e.text || e.tool_name || "")}}
            </div>
        </div>`;
    }}).join("");

    const evidence = t.evidence
        .map(x => "• " + escapeHTML(x))
        .join("<br>");

    detail.innerHTML = `
        <h1>${{escapeHTML(t.title)}}</h1>

        <div class="meta">
            ${{escapeHTML(providers(t))}}
        </div>

        <div class="state">
            ${{escapeHTML(t.state)}}
        </div>

        <div class="stats">
            <div>
                <div class="number">${{t.conversations}}</div>
                <div class="stat-label">conversations</div>
            </div>

            <div>
                <div class="number">${{t.human_turns}}</div>
                <div class="stat-label">human turns</div>
            </div>

            <div>
                <div class="number">${{t.agent_turns}}</div>
                <div class="stat-label">agent turns</div>
            </div>
        </div>

        <div class="section">Evolution</div>
        ${{events}}

        <div class="section">
            Temperans evidence
        </div>

        <div class="evidence">
            ${{evidence || "No evidence recorded."}}
        </div>
    `;
}}

trajectories.forEach((t, index) => {{
    const button = document.createElement("button");

    button.className = "item";
    button.dataset.index = index;

    button.innerHTML = `
        <div class="item-title">
            ${{escapeHTML(t.title)}}
        </div>

        <div class="meta">
            ${{escapeHTML(providers(t))}}
            <br>
            ${{t.conversations}} conversation(s)
            · ${{escapeHTML(t.state)}}
        </div>
    `;

    button.onclick = () => render(t, index);

    list.appendChild(button);
}});

if (trajectories.length) {{
    render(trajectories[0], 0);
}}
</script>

</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--db", required=True)
    parser.add_argument("--user", required=True)
    parser.add_argument("--trajectory", required=True)
    parser.add_argument("--port", type=int, default=8787)

    args = parser.parse_args()

    data = load_trajectories(
        args.db,
        args.user,
        args.trajectory,
    )

    content = page(data).encode("utf-8")

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header(
                "Content-Type",
                "text/html; charset=utf-8",
            )
            self.send_header(
                "Content-Length",
                str(len(content)),
            )
            self.end_headers()
            self.wfile.write(content)

        def log_message(self, *args):
            return

    server = HTTPServer(
        ("127.0.0.1", args.port),
        Handler,
    )

    print()
    print("TEMPERANS TRAJECTORY EXPLORER")
    print(f"http://127.0.0.1:{args.port}")
    print()
    print("Ctrl+C to stop")

    server.serve_forever()


if __name__ == "__main__":
    main()
