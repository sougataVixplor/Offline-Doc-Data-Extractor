"""
applicatiom.py
Entrypoint alias for api.py
"""
from api import app, extractor

if __name__ == "__main__":
    server_cfg = extractor.config.get("server", {})
    host = server_cfg.get("host", "0.0.0.0")
    port = int(server_cfg.get("port", 5000))
    debug = server_cfg.get("debug", False)

    print(f"\n* Starting KYC Document Extraction Server at http://127.0.0.1:{port}")
    print(f"* OCR Engine: {extractor.ocr_engine.preferred_engine.upper()} (Offline)")
    print(f"* Security: 80% Black-box masking enabled | Original images auto-purged")
    print(f"* Memory Optimized for 2-4GB RAM Servers\n")

    app.run(host=host, port=port, debug=debug)
