import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown } from 'lucide-react';
import type { FoodGroup } from '../../data/pyramidData';

interface TierCardProps {
  group: FoodGroup;
}

export const TierCard = ({ group }: TierCardProps) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-6 text-left hover:bg-gray-50 transition-colors duration-200 flex justify-between items-center"
      >
        <div>
          <h4 className="text-xl font-semibold text-dark-green mb-2">
            {group.name}
          </h4>
          <p className="text-gray-600">{group.description}</p>
        </div>
        <motion.div
          animate={{ rotate: isExpanded ? 180 : 0 }}
          transition={{ duration: 0.3 }}
        >
          <ChevronDown className="text-light-green" size={24} />
        </motion.div>
      </button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
            className="border-t border-gray-200 bg-gray-50"
          >
            <div className="p-6">
              {group.servingRecommendation && (
                <p className="text-sm font-semibold text-dark-green mb-4">
                  Recommended: {group.servingRecommendation}
                </p>
              )}
              <div className="mb-4">
                <h5 className="font-semibold text-dark-green mb-3">Common Items:</h5>
                <div className="flex flex-wrap gap-2">
                  {group.items.map((item) => (
                    <span
                      key={item}
                      className="bg-light-green text-white px-3 py-1 rounded-full text-sm"
                    >
                      {item}
                    </span>
                  ))}
                </div>
              </div>
              {group.imagePlaceholder && (
                <img
                  src={`https://images.unsplash.com/photo-1488459716781-6f3f3c9f7d78?w=400&h=300&fit=crop`}
                  alt={group.name}
                  className="w-full h-32 object-cover rounded-lg mt-4"
                />
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default TierCard;
