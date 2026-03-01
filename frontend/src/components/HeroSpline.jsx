import { Suspense, lazy } from "react";
import { motion } from "framer-motion";

const LazySpline = lazy(() => import("@splinetool/react-spline"));

const DEFAULT_SCENE = "https://prod.spline.design/6Wq1Q7YGyM-iab9i/scene.splinecode";

export default function HeroSpline() {
  const scene = import.meta.env.VITE_SPLINE_SCENE_URL || DEFAULT_SCENE;

  return (
    <motion.div
      className="spline-shell"
      initial={{ opacity: 0, scale: 0.92, y: 24 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
    >
      <Suspense fallback={<div className="spline-loading">Loading scene...</div>}>
        <LazySpline scene={scene} />
      </Suspense>
      <div className="spline-vignette" />
    </motion.div>
  );
}
