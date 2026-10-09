import { useEffect, useRef, useState } from "react";
import { CloudUpload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { analyzeInscription, type InscriptionResult } from "@/lib/inscription-analysis";

export function InscriptionWorkspace() {
  const input = useRef<HTMLInputElement>(null);
  const activeRequest = useRef<AbortController | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [result, setResult] = useState<InscriptionResult | null>(null);
  const [error, setError] = useState("");

  useEffect(
    () => () => {
      activeRequest.current?.abort();
    },
    [],
  );
  useEffect(
    () => () => {
      if (preview) URL.revokeObjectURL(preview);
    },
    [preview],
  );

  async function upload(file?: File) {
    if (!file) return;
    if (!/\.(png|jpe?g)$/i.test(file.name)) {
      setError("Please select a PNG, JPG, or JPEG image.");
      return;
    }
    activeRequest.current?.abort();
    const controller = new AbortController();
    activeRequest.current = controller;
    setPreview(URL.createObjectURL(file));
    setResult(null);
    setError("");
    setBusy(true);
    try {
      const output = await analyzeInscription(file, controller.signal);
      if (!controller.signal.aborted) setResult(output);
    } catch (cause) {
      if (!controller.signal.aborted)
        setError(cause instanceof Error ? cause.message : "The image could not be analyzed.");
    } finally {
      if (!controller.signal.aborted) setBusy(false);
    }
  }

  return (
    <div className="workspace screen-enter">
      <div
        className={`upload-zone${dragging ? " is-dragging" : ""}`}
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setDragging(false);
          void upload(event.dataTransfer.files[0]);
        }}
      >
        <input
          ref={input}
          type="file"
          accept=".png,.jpg,.jpeg,image/png,image/jpeg"
          className="sr-only"
          aria-label="Upload inscription image"
          onChange={(event) => {
            void upload(event.target.files?.[0]);
            event.target.value = "";
          }}
        />
        <Button
          variant="ghost"
          className="upload-trigger"
          onClick={() => input.current?.click()}
          aria-label={preview ? "Replace inscription image" : "Upload your image"}
        >
          {preview ? (
            <img className="upload-preview" src={preview} alt="Uploaded inscription" />
          ) : (
            <CloudUpload className="upload-icon" />
          )}
          <span className="upload-label">{preview ? "Change image" : "Upload your image"}</span>
          <span className="upload-caption">"upload image of the inscription"</span>
        </Button>
      </div>
      <section className="result-panel" aria-label="Inscription analysis" aria-busy={busy}>
        <h2 className="result-label">Prachalit transcription:</h2>
        <div
          className="result-field"
          role="region"
          aria-label="Prachalit transcription"
          tabIndex={0}
          aria-live="polite"
        >
          {busy ? <span className="analysis-status">analyzing...</span> : result?.rawOcr}
        </div>
        <h2 className="result-label summary-label">Devanagari transliteration:</h2>
        <div
          className="result-field"
          role="region"
          aria-label="Devanagari transliteration"
          tabIndex={0}
          aria-live="polite"
        >
          {busy ? <span className="analysis-status">analyzing...</span> : result?.devanagari}
        </div>
        <h2 className="result-label summary-label">Historical analysis:</h2>
        <div
          className="result-field summary-field"
          role="region"
          aria-label="Historical analysis"
          tabIndex={0}
          aria-live="polite"
        >
          {busy ? <span className="analysis-status">analyzing...</span> : result?.analysis}
        </div>
        {error && (
          <p className="analysis-error" role="alert">
            {error}
          </p>
        )}
      </section>
    </div>
  );
}
