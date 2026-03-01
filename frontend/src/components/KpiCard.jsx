import { motion } from "framer-motion";

export default function KpiCard({ label, value, accent = "sun", delay = 0 }) {
  return (
    <motion.article
      className={`kpi-card ${accent}`}
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      whileHover={{ y: -8, scale: 1.015 }}
      transition={{
        opacity: { duration: 0.45, delay },
        y: { duration: 0.45, delay },
        scale: { duration: 0.25 },
      }}
      viewport={{ once: true, amount: 0.35 }}
    >
      <p className="kpi-label">{label}</p>
      <p className="kpi-value">{value}</p>
    </motion.article>
  );
}
