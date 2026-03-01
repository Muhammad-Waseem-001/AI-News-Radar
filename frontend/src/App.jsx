import { Suspense, lazy, useEffect, useMemo, useState } from "react";
import dayjs from "dayjs";
import {
  AnimatePresence,
  motion,
  useReducedMotion,
  useScroll,
  useSpring,
  useTransform,
} from "framer-motion";
import KpiCard from "./components/KpiCard";
import HeroSpline from "./components/HeroSpline";
import { fetchArticles, fetchStats, runIngestion } from "./api";

const SENTIMENT_OPTIONS = ["", "positive", "neutral", "negative"];
const SentimentChart = lazy(() => import("./components/SentimentChart"));

function sentimentClass(label) {
  if (label === "positive") return "pill-positive";
  if (label === "negative") return "pill-negative";
  return "pill-neutral";
}

export default function App() {
  const [stats, setStats] = useState({
    total_articles: 0,
    sources: 0,
    avg_sentiment: 0,
    sentiment_breakdown: { positive: 0, neutral: 0, negative: 0 },
    categories: {},
  });
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [ingesting, setIngesting] = useState(false);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState(null);

  const [filters, setFilters] = useState({
    sentiment: "",
    category: "",
    source: "",
  });

  const shouldReduceMotion = useReducedMotion();
  const { scrollYProgress } = useScroll();
  const scrollScaleX = useSpring(scrollYProgress, { stiffness: 140, damping: 28, mass: 0.25 });
  const orbY = useTransform(scrollYProgress, [0, 1], [0, shouldReduceMotion ? 0 : -180]);
  const orbRotate = useTransform(scrollYProgress, [0, 1], [0, shouldReduceMotion ? 0 : 36]);

  const categoryOptions = useMemo(() => ["", ...Object.keys(stats.categories || {})], [stats.categories]);
  const sourceOptions = useMemo(() => ["", ...new Set(articles.map((item) => item.source))], [articles]);

  const chartData = useMemo(() => {
    const breakdown = stats.sentiment_breakdown || {};
    return [
      { label: "Positive", count: breakdown.positive || 0 },
      { label: "Neutral", count: breakdown.neutral || 0 },
      { label: "Negative", count: breakdown.negative || 0 },
    ];
  }, [stats.sentiment_breakdown]);

  async function loadData(activeFilters) {
    try {
      setError("");
      setLoading(true);
      const [statsData, articleData] = await Promise.all([
        fetchStats(),
        fetchArticles({
          limit: 100,
          sentiment: activeFilters.sentiment,
          category: activeFilters.category,
          source: activeFilters.source,
        }),
      ]);
      setStats(statsData);
      setArticles(articleData);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err?.message || "Failed to load dashboard data.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData(filters);
    const timer = setInterval(() => loadData(filters), 60000);
    return () => clearInterval(timer);
  }, [filters]);

  async function handleIngestNow() {
    try {
      setIngesting(true);
      await runIngestion();
      await loadData(filters);
    } catch (err) {
      setError(err?.message || "Failed to trigger ingestion.");
    } finally {
      setIngesting(false);
    }
  }

  function onFilterChange(key, value) {
    setFilters((current) => ({ ...current, [key]: value }));
  }

  return (
    <main className="app-shell">
      <motion.div className="scroll-progress" style={{ scaleX: scrollScaleX }} />
      <motion.div className="ambient-orb" style={{ y: orbY, rotate: orbRotate }} />

      <motion.header
        className="hero"
        initial={{ opacity: 0, y: 28 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      >
        <div className="hero-copy">
          <p className="eyebrow">AI Intelligence Surface</p>
          <h1>Sentiment Radar Command Deck</h1>
          <p className="subcopy">
            An animated monitoring layer for AI headlines, impact classification, and risk-triggered Gmail alerts.
          </p>
          <div className="hero-actions">
            <motion.button
              className="btn btn-primary"
              onClick={handleIngestNow}
              disabled={ingesting}
              whileHover={{ scale: 1.04, y: -2 }}
              whileTap={{ scale: 0.98 }}
            >
              {ingesting ? "Ingesting..." : "Run Ingestion Now"}
            </motion.button>
            <p className="timestamp">
              Last updated: {lastUpdated ? dayjs(lastUpdated).format("YYYY-MM-DD HH:mm:ss") : "Never"}
            </p>
          </div>
        </div>
        <div className="hero-scene">
          <HeroSpline />
        </div>
      </motion.header>

      <AnimatePresence mode="wait">
        {error ? (
          <motion.p
            key={error}
            className="error-banner"
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
          >
            {error}
          </motion.p>
        ) : null}
      </AnimatePresence>

      <section className="kpi-grid">
        <KpiCard label="Total Articles" value={stats.total_articles} accent="sun" delay={0.02} />
        <KpiCard label="Tracked Sources" value={stats.sources} accent="sea" delay={0.1} />
        <KpiCard
          label="Average Sentiment"
          value={Number(stats.avg_sentiment || 0).toFixed(2)}
          accent="storm"
          delay={0.18}
        />
      </section>

      <motion.section
        className="filters panel"
        initial={{ opacity: 0, y: 24 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45 }}
        viewport={{ once: true, amount: 0.2 }}
      >
        <div className="panel-head">
          <h3>Signal Filters</h3>
          <p>Refine source, category, and tone</p>
        </div>
        <div className="filter-grid">
          <label>
            Sentiment
            <select
              value={filters.sentiment}
              onChange={(event) => onFilterChange("sentiment", event.target.value)}
            >
              {SENTIMENT_OPTIONS.map((option) => (
                <option key={option || "all"} value={option}>
                  {option ? option : "all"}
                </option>
              ))}
            </select>
          </label>
          <label>
            Category
            <select
              value={filters.category}
              onChange={(event) => onFilterChange("category", event.target.value)}
            >
              {categoryOptions.map((option) => (
                <option key={option || "all"} value={option}>
                  {option ? option : "all"}
                </option>
              ))}
            </select>
          </label>
          <label>
            Source
            <select value={filters.source} onChange={(event) => onFilterChange("source", event.target.value)}>
              {sourceOptions.map((option) => (
                <option key={option || "all"} value={option}>
                  {option ? option : "all"}
                </option>
              ))}
            </select>
          </label>
        </div>
      </motion.section>

      <section className="content-grid">
        <Suspense fallback={<section className="panel chart-panel chart-loading">Loading chart...</section>}>
          <SentimentChart data={chartData} />
        </Suspense>

        <motion.section
          className="panel article-panel"
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          viewport={{ once: true, amount: 0.15 }}
        >
          <div className="panel-head">
            <h3>Latest Articles</h3>
            <p>{loading ? "Syncing live feed..." : `${articles.length} records`}</p>
          </div>

          <div className="article-list">
            <AnimatePresence mode="popLayout">
              {articles.map((article, index) => (
                <motion.article
                  key={article.id}
                  layout
                  className="article-card"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -16 }}
                  transition={{ duration: 0.28, delay: index < 10 ? index * 0.018 : 0 }}
                  whileHover={{ y: -6, scale: 1.01 }}
                >
                  <div className="article-meta">
                    <span className={`pill ${sentimentClass(article.sentiment_label)}`}>
                      {article.sentiment_label} ({article.sentiment_score.toFixed(2)})
                    </span>
                    <span className="meta-source">{article.source}</span>
                    <span>{article.category}</span>
                  </div>
                  <h4>{article.title}</h4>
                  <p>{article.summary}</p>
                  <div className="article-foot">
                    <span>{article.published_at ? dayjs(article.published_at).format("YYYY-MM-DD HH:mm") : "N/A"}</span>
                    <a href={article.link} target="_blank" rel="noreferrer">
                      Read
                    </a>
                  </div>
                </motion.article>
              ))}
            </AnimatePresence>
            {!loading && articles.length === 0 ? <p className="empty">No records found for selected filters.</p> : null}
          </div>
        </motion.section>
      </section>
    </main>
  );
}
