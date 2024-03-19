from dotenv import load_dotenv
from openai import OpenAI

from streaming_assistants import patch

load_dotenv("./.env")
client = patch(OpenAI())

def create_assistant(file_ids):
    system_prompt = """
You are a developer, you will be provided with a partial code base and a github issue description explaining a programming problem to resolve.
Solve the issue by generating a single patch file that can be applied directly to this repository using git apply. Please respond with a single patch file in the following format (no yapping).
<patch>
--- a/file.py
+++ b/file.py
@@ -1,27 +1,35 @@
def euclidean(a, b):
-    while b:
-        a, b = b, a % b
-    return a
+    if b == 0:
+        return a
+    return euclidean(b, a % b)


def bresenham(x0, y0, x1, y1):
points = []
dx = abs(x1 - x0)
dy = abs(y1 - y0)
-    sx = 1 if x0 < x1 else -1
-    sy = 1 if y0 < y1 else -1
-    err = dx - dy
+    x, y = x0, y0
+    sx = -1 if x0 > x1 else 1
+    sy = -1 if y0 > y1 else 1

-    while True:
-        points.append((x0, y0))
-        if x0 == x1 and y0 == y1:
-            break
-        e2 = 2 * err
-        if e2 > -dy:
+    if dx > dy:
+        err = dx / 2.0
+        while x != x1:
+            points.append((x, y))
err -= dy
-            x0 += sx
-        if e2 < dx:
-            err += dx
-            y0 += sy
+            if err < 0:
+                y += sy
+                err += dx
+            x += sx
+    else:
+        err = dy / 2.0
+        while y != y1:
+            points.append((x, y))
+            err -= dx
+            if err < 0:
+                x += sx
+                err += dy
+            y += sy

+    points.append((x, y))
return points
</patch>
"""
       # create assistant
    assistant = client.beta.assistants.create(
    file_ids=file_ids,
    model="text-embedding-3-large",
    instructions=system_prompt,
    name="retrieval-assisted-coder",
    tools=[{"type": "retrieval"}],
    )
    return assistant


def run_inference(assistant_id, row_data):
    user_prompt = f"""
    <issue>
    {row_data["problem_statement"]}
    </issue>
    """
    print("creating persistent thread and message")
    thread = client.beta.threads.create()
    client.beta.threads.messages.create(
        thread_id=thread.id, role="user", content=user_prompt
    )
    print(f"running inference for {row_data['instance_id']}")

    print(f"creating run")
    with client.beta.threads.runs.create_and_stream(
            thread_id=thread.id,
            assistant_id=assistant_id,
    ) as stream:
        for text in stream.text_deltas:
            print(text, end="", flush=True)
            print()

    print("\n")
