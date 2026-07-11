import { useRef, useState } from "react";
import { UploadCloud, X } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

const ACCEPT = "image/jpeg,image/png,image/webp,application/pdf";

/** Zone de dépôt multi-fichiers (images/PDF), glisser-déposer ou clic. */
export function UploadZone({
  label,
  hint,
  icon: Icon,
  files,
  onChange,
}: {
  label: string;
  hint: string;
  icon: LucideIcon;
  files: File[];
  onChange: (files: File[]) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [drag, setDrag] = useState(false);

  function add(list: FileList | null) {
    if (!list) return;
    onChange([...files, ...Array.from(list)]);
  }

  return (
    <div>
      <div
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDrag(true);
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDrag(false);
          add(e.dataTransfer.files);
        }}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && inputRef.current?.click()}
        className={cn(
          "flex flex-col items-center justify-center gap-2 rounded-2xl border-2 border-dashed px-4 py-6 text-center cursor-pointer transition-colors",
          drag ? "border-accent bg-accent/5" : "border-line hover:border-ink/30 bg-surface",
        )}
      >
        <div className="grid h-10 w-10 place-items-center rounded-xl bg-ink/8 text-ink">
          <Icon size={20} />
        </div>
        <div className="text-sm font-medium text-ink">{label}</div>
        <div className="flex items-center gap-1 text-xs text-muted">
          <UploadCloud size={13} /> {hint}
        </div>
      </div>
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPT}
        multiple
        className="hidden"
        onChange={(e) => add(e.target.files)}
      />
      {files.length > 0 && (
        <ul className="mt-2 space-y-1">
          {files.map((f, i) => (
            <li
              key={`${f.name}-${i}`}
              className="flex items-center justify-between rounded-lg bg-ink/5 px-3 py-1.5 text-xs text-ink"
            >
              <span className="truncate">{f.name}</span>
              <button
                type="button"
                onClick={() => onChange(files.filter((_, j) => j !== i))}
                className="text-muted hover:text-score-zero"
                aria-label="Retirer"
              >
                <X size={14} />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
