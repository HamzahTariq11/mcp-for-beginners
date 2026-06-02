import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export function Markdown({ children }: { children: string }) {
  return (
    <div className="space-y-3 text-[15px] leading-relaxed text-foreground">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: (p) => <h1 className="mt-2 text-2xl font-semibold" {...p} />,
          h2: (p) => <h2 className="mt-2 text-xl font-semibold" {...p} />,
          h3: (p) => <h3 className="mt-2 text-lg font-semibold" {...p} />,
          p: (p) => <p className="leading-relaxed" {...p} />,
          ul: (p) => <ul className="ml-5 list-disc space-y-1" {...p} />,
          ol: (p) => <ol className="ml-5 list-decimal space-y-1" {...p} />,
          li: (p) => <li className="leading-relaxed" {...p} />,
          strong: (p) => <strong className="font-semibold text-foreground" {...p} />,
          a: (p) => <a className="text-primary underline underline-offset-2" {...p} />,
          code: ({ className, children, ...rest }) => {
            const inline = !className;
            if (inline) {
              return (
                <code
                  className="rounded bg-secondary px-1.5 py-0.5 font-mono text-[13px] text-primary"
                  {...rest}
                >
                  {children}
                </code>
              );
            }
            return (
              <code className={`font-mono text-[13px] ${className ?? ""}`} {...rest}>
                {children}
              </code>
            );
          },
          pre: (p) => (
            <pre
              className="overflow-x-auto rounded-lg border border-border bg-secondary p-3 font-mono text-[13px]"
              {...p}
            />
          ),
          table: (p) => (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-sm" {...p} />
            </div>
          ),
          th: (p) => (
            <th className="border border-border bg-secondary px-3 py-1.5 text-left font-semibold" {...p} />
          ),
          td: (p) => <td className="border border-border px-3 py-1.5" {...p} />,
          blockquote: (p) => (
            <blockquote className="border-l-2 border-primary pl-3 text-muted-foreground" {...p} />
          ),
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}