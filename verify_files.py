import os
import sys

def verify_project_structure():
    errors = []
    
    # Check directories
    required_dirs = ['static', 'letters']
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            errors.append(f"Directory '{dir_name}' not found")
    
    # Check static files
    required_static_files = [
        'index.html',
        'TALKING_SANDY.gif',
        'WAITING_SANDY.gif',
        'Question_SANDY.gif'
    ]
    
    for file_name in required_static_files:
        file_path = os.path.join('static', file_name)
        if not os.path.exists(file_path):
            errors.append(f"Static file '{file_name}' not found")
    
    # Check configuration files
    required_config_files = [
        'vercel.json',
        'requirements.txt',
        'app.py',
        'main.py'
    ]
    
    for file_name in required_config_files:
        if not os.path.exists(file_name):
            errors.append(f"Configuration file '{file_name}' not found")
    
    # Check letters directory content
    required_letters = [
        'a.wav', 'b.wav', 'c.wav', 'd.wav', 'e.wav',
        'f.wav', 'g.wav', 'h.wav', 'i.wav', 'j.wav',
        'k.wav', 'l.wav', 'm.wav', 'n.wav', 'o.wav',
        'p.wav', 'q.wav', 'r.wav', 's.wav', 't.wav',
        'u.wav', 'v.wav', 'w.wav', 'x.wav', 'y.wav',
        'z.wav', 'ch.wav', 'sh.wav', 'ph.wav', 'th.wav',
        'wh.wav', 'bebebese.wav', 'bebebese_slow.wav'
    ]
    
    for file_name in required_letters:
        file_path = os.path.join('letters', file_name)
        if not os.path.exists(file_path):
            errors.append(f"Letter sound file '{file_name}' not found")
    
    # Print results
    if errors:
        print("❌ Project verification failed!")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("✅ Project verification passed!")
        print("\nDirectory structure:")
        for dir_name in required_dirs:
            if os.path.exists(dir_name):
                print(f"\n{dir_name}/")
                for file in os.listdir(dir_name):
                    print(f"  - {file}")

if __name__ == "__main__":
    verify_project_structure() 