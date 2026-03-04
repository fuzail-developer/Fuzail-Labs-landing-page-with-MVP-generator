// app/page.tsx (Next.js)
import { motion } from 'framer-motion';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0a14] via-[#0f0f1a] to-[#0a0a14] text-white overflow-hidden relative">
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-[-20%] left-[-20%] w-[60%] h-[60%] bg-[radial-gradient(circle,rgba(88,28,135,0.25),transparent_60%)] animate-pulse" />
        <div className="absolute bottom-[-20%] right-[-20%] w-[60%] h-[60%] bg-[radial-gradient(circle,rgba(49,46,129,0.25),transparent_60%)] animate-pulse" />
      </div>

      <section className="relative pt-32 pb-20 px-6 md:px-12 lg:px-24 text-center z-10">
        <motion.h1
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, ease: 'easeOut' }}
          className="text-5xl md:text-7xl font-black tracking-tight mb-6"
        >
          <span className="bg-gradient-to-r from-purple-400 via-indigo-400 to-blue-400 bg-clip-text text-transparent">
            Build Your SaaS MVP
          </span>
          <br />
          <span className="text-4xl md:text-6xl">in 24-48 Hours Using AI</span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.8 }}
          className="text-xl md:text-2xl text-gray-300 max-w-3xl mx-auto mb-12"
        >
          FOR FOUNDERS WHO WANT TO VALIDATE FAST WITHOUT HIRING A DEV TEAM.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.6, duration: 0.5 }}
          className="flex flex-col sm:flex-row gap-6 justify-center"
        >
          <a
            href="#order"
            className="px-10 py-5 bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-black font-bold text-xl rounded-xl shadow-2xl transform hover:scale-105 transition-all duration-300 flex items-center justify-center gap-3"
          >
            Start Your MVP Now - From $79
          </a>
          <a
            href="#contact"
            className="px-10 py-5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-bold text-xl rounded-xl shadow-2xl transform hover:scale-105 transition-all duration-300 flex items-center justify-center gap-3"
          >
            Book Free Scope Call
          </a>
        </motion.div>
      </section>

      <section className="relative py-20 px-6 md:px-12 lg:px-24 z-10">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="pricing-card bg-gradient-to-b from-gray-900/80 to-black/80 backdrop-blur-xl border border-purple-500/30 rounded-3xl p-8 shadow-2xl hover:shadow-purple-500/40 transition-all duration-500 group relative overflow-hidden"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-purple-900/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            <h3 className="text-3xl font-black text-white mb-4 text-center">Basic MVP</h3>
            <div className="text-5xl font-extrabold text-center mb-8 bg-gradient-to-r from-purple-400 to-indigo-400 bg-clip-text text-transparent">
              $79
            </div>
            <ul className="space-y-4 text-gray-300 text-lg">
              <li className="flex items-center gap-3"><span className="text-purple-400 text-xl">?</span> Landing + one core flow</li>
              <li className="flex items-center gap-3"><span className="text-purple-400 text-xl">?</span> Basic DB model</li>
              <li className="flex items-center gap-3"><span className="text-purple-400 text-xl">?</span> 1 revision</li>
            </ul>
            <button className="mt-10 w-full py-5 bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-black font-bold text-xl rounded-xl shadow-lg hover:shadow-2xl transform hover:scale-105 transition-all duration-300">
              Start Basic MVP - $79
            </button>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.3 }}
            className="pricing-card relative bg-gradient-to-b from-purple-950/80 to-indigo-950/80 backdrop-blur-xl border-2 border-purple-500 rounded-3xl p-8 shadow-2xl hover:shadow-purple-600/50 transition-all duration-500 group scale-105 z-20"
          >
            <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-purple-600 text-white px-6 py-2 rounded-full font-bold text-sm shadow-lg">
              RECOMMENDED
            </div>
            <h3 className="text-3xl font-black text-white mb-4 text-center">Startup MVP</h3>
            <div className="text-5xl font-extrabold text-center mb-8 bg-gradient-to-r from-purple-300 to-indigo-300 bg-clip-text text-transparent">
              $149
            </div>
            <ul className="space-y-4 text-gray-200 text-lg">
              <li className="flex items-center gap-3"><span className="text-purple-400 text-xl">?</span> Auth + dashboard + admin basics</li>
              <li className="flex items-center gap-3"><span className="text-purple-400 text-xl">?</span> Deploy-ready setup</li>
              <li className="flex items-center gap-3"><span className="text-purple-400 text-xl">?</span> 2 revisions</li>
            </ul>
            <button className="mt-10 w-full py-5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white font-bold text-xl rounded-xl shadow-lg hover:shadow-2xl transform hover:scale-105 transition-all duration-300">
              Start Startup MVP - $149
            </button>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.5 }}
            className="pricing-card bg-gradient-to-b from-gray-900/80 to-black/80 backdrop-blur-xl border border-purple-500/30 rounded-3xl p-8 shadow-2xl hover:shadow-purple-500/40 transition-all duration-500 group relative overflow-hidden"
          >
            <h3 className="text-3xl font-black text-white mb-4 text-center">Full SaaS</h3>
            <div className="text-5xl font-extrabold text-center mb-8 bg-gradient-to-r from-purple-400 to-indigo-400 bg-clip-text text-transparent">
              $399
            </div>
            <ul className="space-y-4 text-gray-300 text-lg">
              <li className="flex items-center gap-3"><span className="text-purple-400 text-xl">?</span> Complete SaaS architecture</li>
              <li className="flex items-center gap-3"><span className="text-purple-400 text-xl">?</span> Admin workflow + analytics</li>
              <li className="flex items-center gap-3"><span className="text-purple-400 text-xl">?</span> Priority delivery</li>
            </ul>
            <button className="mt-10 w-full py-5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-bold text-xl rounded-xl shadow-lg hover:shadow-2xl transform hover:scale-105 transition-all duration-300">
              Start Full SaaS - $399
            </button>
          </motion.div>
        </div>
      </section>
    </div>
  );
}
