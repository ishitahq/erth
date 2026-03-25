import { motion } from 'framer-motion';

const pipelineSteps = [
  {
    step: "01",
    title: "Data Collection",
    description: "Gather diverse plastic waste images from public datasets and custom sources covering all 6 categories under various conditions.",
    icon: "📂",
    color: "from-blue-500 to-blue-600"
  },
  {
    step: "02",
    title: "Preprocessing & Augmentation",
    description: "Resize, normalize, and augment images with rotation, flipping, noise, and color jitter to simulate real-world conditions.",
    icon: "🔄",
    color: "from-purple-500 to-purple-600"
  },
  {
    step: "03",
    title: "Model Training",
    description: "Train a CNN using transfer learning (ResNet/EfficientNet) with fine-tuning on the plastic waste dataset for optimal accuracy.",
    icon: "🧠",
    color: "from-emerald-500 to-emerald-600"
  },
  {
    step: "04",
    title: "Evaluation & Optimization",
    description: "Evaluate with accuracy, precision, recall, and confusion matrix. Optimize thresholds and apply model pruning for deployment.",
    icon: "📊",
    color: "from-amber-500 to-amber-600"
  },
  {
    step: "05",
    title: "Deployment",
    description: "Deploy as a web application, REST API, or edge device integration for real-time classification in recycling facilities.",
    icon: "🚀",
    color: "from-rose-500 to-rose-600"
  }
];

export const PipelineSection = () => {
  return (
    <section id="pipeline" className="section-cream section-padding">
      <div className="section-container">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.2 }}
          transition={{ duration: 0.8 }}
          className="mb-12 md:mb-20"
        >
          <p className="text-emerald-600 text-sm md:text-base uppercase tracking-widest mb-4 font-semibold">
            ML Pipeline
          </p>
          <h2 className="heading-section-dark mb-6">
            How It Works
          </h2>
          <p className="text-base md:text-lg text-site-text-dark/60 max-w-3xl leading-relaxed">
            From raw plastic waste images to accurate classification — a complete end-to-end
            machine learning pipeline.
          </p>
        </motion.div>

        {/* Pipeline Steps */}
        <div className="relative max-w-4xl mx-auto">
          {/* Connecting Line */}
          <div className="absolute left-8 md:left-12 top-0 bottom-0 w-0.5 bg-gradient-to-b from-blue-500 via-emerald-500 to-rose-500 hidden md:block" />

          {pipelineSteps.map((step, index) => (
            <motion.div
              key={step.step}
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: index * 0.15, ease: [0.25, 0.46, 0.45, 0.94] }}
              className="relative flex items-start gap-6 mb-12 last:mb-0"
            >
              {/* Step Number Circle */}
              <div className={`flex-shrink-0 w-16 h-16 md:w-24 md:h-24 rounded-2xl bg-gradient-to-br ${step.color} flex items-center justify-center shadow-lg relative z-10`}>
                <span className="text-2xl md:text-4xl">{step.icon}</span>
              </div>

              {/* Content */}
              <div className="pt-1 md:pt-4">
                <div className="flex items-center gap-3 mb-2">
                  <span className="text-xs font-bold text-site-text-dark/30 uppercase tracking-widest">
                    Step {step.step}
                  </span>
                </div>
                <h3 className="text-xl md:text-2xl font-bold text-site-text-dark mb-2">
                  {step.title}
                </h3>
                <p className="text-sm md:text-base text-site-text-dark/60 leading-relaxed max-w-lg">
                  {step.description}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default PipelineSection;
