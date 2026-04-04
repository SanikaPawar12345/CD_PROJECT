import { motion } from 'framer-motion'

export default function TokenView({ tokens = [] }) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="bg-card border border-white/10 rounded-xl overflow-hidden"
    >
      <div className="px-5 py-3 border-b border-white/10">
        <h3 className="text-base font-semibold">Step 1: Tokenization Phase</h3>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-bg/50">
            <tr className="text-left border-b border-white/10">
              <th className="px-4 py-3 text-secondary font-medium">#</th>
              <th className="px-4 py-3 text-secondary font-medium">Token Type</th>
              <th className="px-4 py-3 text-secondary font-medium">Token Value</th>
            </tr>
          </thead>
          <tbody>
            {tokens.map((token, index) => (
              <tr key={`${token.type}-${index}`} className="border-b border-white/5">
                <td className="px-4 py-3 text-secondary font-mono">{index + 1}</td>
                <td className="px-4 py-3 font-mono text-cyan">{token.type}</td>
                <td className="px-4 py-3 font-mono text-primary">{String(token.value ?? '')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </motion.section>
  )
}
