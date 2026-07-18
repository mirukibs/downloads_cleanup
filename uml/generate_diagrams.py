import os
import urllib.request
import json

def render_plantuml(puml_path, output_svg_path):
    print(f"Rendering {puml_path}...")
    with open(puml_path, 'r', encoding='utf-8') as f:
        puml_content = f.read()
    
    url = "https://kroki.io/"
    payload = json.dumps({
        "diagram_source": puml_content,
        "diagram_type": "plantuml",
        "output_format": "svg"
    }).encode('utf-8')
    
    req = urllib.request.Request(url, data=payload, method='POST')
    req.add_header('Content-Type', 'application/json')
    req.add_header('User-Agent', 'Mozilla/5.0')
    
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                with open(output_svg_path, 'wb') as f:
                    f.write(response.read())
                print(f"Successfully generated {output_svg_path}")
            else:
                print(f"Failed to generate diagram: HTTP {response.status}")
    except Exception as e:
        print(f"Failed to generate diagram: {e}")

if __name__ == "__main__":
    uml_dir = "docs/uml"
    img_dir = "docs/images"
    
    for filename in os.listdir(uml_dir):
        if filename.endswith(".puml"):
            puml_path = os.path.join(uml_dir, filename)
            svg_name = filename.replace(".puml", ".svg")
            output_svg_path = os.path.join(img_dir, svg_name)
            render_plantuml(puml_path, output_svg_path)
