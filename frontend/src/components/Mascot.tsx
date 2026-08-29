interface MascotProps {
  size?: number;
  thinking?: boolean;
  className?: string;
}

/**
 * Mika's mark. A calm abstract cluster rather than a cartoon character - it has
 * to read as a tool a 10-year-old is not embarrassed to use.
 */
export default function Mascot({ size = 44, thinking = false, className = "" }: MascotProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      aria-hidden="true"
      className={className}
    >
      <g className="text-muted" opacity="0.85">
        <circle cx="16" cy="18" r="11" fill="currentColor" opacity="0.28" />
        <circle cx="32" cy="18" r="11" fill="currentColor" opacity="0.28" />
        <circle cx="24" cy="28" r="12" fill="currentColor" opacity="0.28" />
      </g>
      <circle cx="19.5" cy="24" r="2.1" className="text-ink" fill="currentColor">
        {thinking && (
          <animate attributeName="cy" values="24;22.6;24" dur="1.6s" repeatCount="indefinite" />
        )}
      </circle>
      <circle cx="28.5" cy="24" r="2.1" className="text-ink" fill="currentColor">
        {thinking && (
          <animate
            attributeName="cy"
            values="24;22.6;24"
            dur="1.6s"
            begin="0.2s"
            repeatCount="indefinite"
          />
        )}
      </circle>
    </svg>
  );
}
