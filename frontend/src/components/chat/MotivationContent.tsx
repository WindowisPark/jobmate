interface Video {
  title?: string;
  url?: string;
  videoId?: string;
}

interface Quote {
  text?: string;
  author?: string;
}

interface MotivationContentProps {
  data: {
    mood?: string;
    videos?: Video[];
    quotes?: Quote[];
  };
}

function extractVideoId(url: string): string | null {
  const match = url.match(
    /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})/
  );
  return match ? match[1]! : null;
}

export default function MotivationContent({ data }: MotivationContentProps) {
  const videos = data.videos || [];
  const quotes = data.quotes || [];

  if (!videos.length && !quotes.length) return null;

  return (
    <div style={{ margin: "8px 0" }}>
      {/* 명언 카드 */}
      {quotes.map((quote, i) => (
        <div
          key={i}
          style={{
            background: "linear-gradient(135deg, rgba(229,192,123,0.1), rgba(229,192,123,0.05))",
            border: "1px solid rgba(229,192,123,0.3)",
            borderRadius: "var(--radius-lg)",
            padding: "16px 20px",
            margin: "8px 0",
            position: "relative",
          }}
        >
          <div
            style={{
              fontSize: 24,
              color: "rgba(229,192,123,0.4)",
              position: "absolute",
              top: 8,
              left: 12,
              fontFamily: "Georgia, serif",
            }}
          >
            "
          </div>
          <div
            style={{
              fontSize: "var(--font-base)",
              color: "var(--text-primary)",
              fontStyle: "italic",
              lineHeight: 1.6,
              paddingLeft: 16,
            }}
          >
            {quote.text}
          </div>
          {quote.author && (
            <div
              style={{
                fontSize: "var(--font-sm)",
                color: "var(--text-secondary)",
                textAlign: "right",
                marginTop: 8,
              }}
            >
              — {quote.author}
            </div>
          )}
        </div>
      ))}

      {/* YouTube 임베드 */}
      {videos.map((video, i) => {
        const videoId = video.videoId || (video.url ? extractVideoId(video.url) : null);
        if (!videoId) return null;

        return (
          <div
            key={i}
            style={{
              margin: "8px 0",
              borderRadius: "var(--radius-lg)",
              overflow: "hidden",
              background: "var(--bg-tertiary)",
            }}
          >
            {video.title && (
              <div
                style={{
                  padding: "8px 12px",
                  fontSize: "var(--font-sm)",
                  color: "var(--text-secondary)",
                }}
              >
                {video.title}
              </div>
            )}
            <div style={{ position: "relative", paddingBottom: "56.25%", height: 0 }}>
              <iframe
                src={`https://www.youtube.com/embed/${videoId}`}
                title={video.title || "동기부여 영상"}
                style={{
                  position: "absolute",
                  top: 0,
                  left: 0,
                  width: "100%",
                  height: "100%",
                  border: "none",
                }}
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
                loading="lazy"
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
