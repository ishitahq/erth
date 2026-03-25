export interface PlasticType {
  id: number;
  code: string;
  name: string;
  fullName: string;
  description: string;
  examples: string;
  recyclability: string;
  color: string;
}

export const plasticTypesData: PlasticType[] = [
  {
    id: 1,
    code: "♳",
    name: "PET",
    fullName: "Polyethylene Terephthalate",
    description: "One of the most commonly recycled plastics. Clear, strong, and lightweight. Easily identified by its transparency and smooth texture.",
    examples: "Water bottles, soda bottles, food jars, polyester clothing fibers",
    recyclability: "Highly recyclable — widely accepted in curbside programs",
    color: "from-cyan-500 to-blue-600"
  },
  {
    id: 2,
    code: "♴",
    name: "HDPE",
    fullName: "High-Density Polyethylene",
    description: "A sturdy, opaque plastic resistant to chemicals. Durable and easy to mold. Recognized by its rigid, opaque body and waxy feel.",
    examples: "Milk jugs, detergent bottles, shampoo bottles, grocery bags",
    recyclability: "Highly recyclable — strong demand in secondary markets",
    color: "from-green-500 to-emerald-600"
  },
  {
    id: 3,
    code: "♶",
    name: "LDPE",
    fullName: "Low-Density Polyethylene",
    description: "A flexible, thin plastic that is squeezable and often transparent. Harder to recycle due to its low melting point and tendency to jam machinery.",
    examples: "Plastic bags, shrink wrap, squeeze bottles, bread bags",
    recyclability: "Limited recyclability — not accepted in most curbside programs",
    color: "from-yellow-500 to-amber-600"
  },
  {
    id: 4,
    code: "♷",
    name: "PP",
    fullName: "Polypropylene",
    description: "Heat-resistant and semi-rigid plastic. Commonly used in packaging and automotive parts. Identified by its slightly glossy, flexible yet firm structure.",
    examples: "Yogurt containers, bottle caps, straws, microwave-safe containers",
    recyclability: "Moderately recyclable — growing infrastructure for recycling",
    color: "from-orange-500 to-red-500"
  },
  {
    id: 5,
    code: "♸",
    name: "PS",
    fullName: "Polystyrene",
    description: "Used in both rigid and foam (Styrofoam) forms. Lightweight and brittle. Easily identified by its foam texture or rigid, often transparent form.",
    examples: "Styrofoam cups, takeout containers, CD cases, packing peanuts",
    recyclability: "Rarely recyclable — most facilities reject it",
    color: "from-purple-500 to-violet-600"
  },
  {
    id: 6,
    code: "♹",
    name: "Other",
    fullName: "Mixed / Unknown Plastics",
    description: "Includes multi-layer plastics, polycarbonate, nylon, and other resins not covered by codes 1–6. These plastics are the hardest to identify and recycle.",
    examples: "Baby bottles, CDs, sunglasses, multi-layer food packaging",
    recyclability: "Very difficult to recycle — often sent to landfill",
    color: "from-gray-500 to-gray-700"
  }
];
