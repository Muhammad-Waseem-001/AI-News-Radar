import { motion } from "framer-motion";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export default function SentimentChart({ data }) {
  return (
    <motion.section
      className="panel chart-panel"
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      viewport={{ once: true, amount: 0.35 }}
      whileHover={{ y: -4 }}
    >
      <div className="panel-head">
        <h3>Sentiment Split</h3>
      </div>
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="4 4" stroke="rgba(255,255,255,0.15)" />
            <XAxis dataKey="label" stroke="#cce4ff" />
            <YAxis stroke="#cce4ff" allowDecimals={false} />
            <Tooltip
              cursor={{ fill: "rgba(255, 255, 255, 0.08)" }}
              contentStyle={{
                borderRadius: "12px",
                border: "1px solid rgba(178, 214, 255, 0.3)",
                background: "rgba(7, 18, 32, 0.92)",
                color: "#e6f4ff",
              }}
            />
            <Bar dataKey="count" radius={[8, 8, 0, 0]} fill="#ff8f4f" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </motion.section>
  );
}
