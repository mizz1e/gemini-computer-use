import google.generativeai as genai
import json
import os
import signal
import subprocess
import time

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

while True:
    print("waiting 5 seconds")
    time.sleep(5)

    print("record 5 seconds")
    with subprocess.Popen(["wf-recorder", "-a", "-f", "unknown.mp4", "-y"]) as process:
        try:
            process.wait(timeout=5)
        except:
            process.send_signal(signal.SIGINT)
            process.wait()

    print("upload video")
    video_file = genai.upload_file(path="unknown.mp4")

    while video_file.state.name == "PROCESSING":
        time.sleep(5)
        video_file = genai.get_file(video_file.name)

    if video_file.state.name == "FAILED":
      raise ValueError(video_file.state.name)

    model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")
    prompt = """You are permanently roleplaying as mari - a bored dude on his computer.
    Always think as mari, always respond as mari.
    You are currently looking at your screen, decide what to do next.
    To type a message in Discord, type your message, and press enter. (Use `keyboard_input` and end `action_value` with a newline).
    Type responses lazily, with a lack of punctuation, and punctuation, like a chat user.
    Don't repeat previous responses.
    Respond in JSON with a list of actions to take, following this schema:

    {
      "type": "object",
      "properties": {
        "actions": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "action": {
                "type": "string",
                "enum": [
                  "pointer_button",
                  "pointer_move",
                  "keyboard_input"
                ]
              },
              "action_value": {
                "type": "string"
              }
            }
          }
        }
      }
    }
    """

    print("evaluate actions")
    result = model.generate_content(
        [video_file, prompt],
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema={
              "type": "object",
              "properties": {
                "actions": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "action": {
                        "type": "string",
                        "enum": [
                          "pointer_button",
                          "pointer_move",
                          "keyboard_input"
                        ]
                      },
                      "action_value": {
                        "type": "string"
                      }
                    }
                  }
                }
              }
            },
        ),
    )

    print("actions", result.text)

    actions = json.loads(result.text)

    def keyboard_input(input: str):
        print(f"keyboard_input({input})")

        subprocess.run(["wtype", "-d", "150", input])

    def pointer_move(x: int, y: int):
        print(f"pointer_move({x}, {y})")

        subprocess.run(["wlrctl", "pointer", "move", str(x), str(y)])

    for action in actions["actions"]:
        print(action)

        match action["action"]:
            case "pointer_button":
                pass
            case "pointer_move":
                x, y = map(int, map(int, action["action_value"].split(",")))

                pointer_move(x, y)
            case "keyboard_input":
                keyboard_input(action["action_value"])
