export interface Statistic {
  id: number;
  percentage: number;
  label: string;
  highlight: string;
}

export const statisticsData: Statistic[] = [
  {
    id: 1,
    percentage: 36,
    label: "Only 36% of plastic packaging is",
    highlight: "collected for recycling"
  },
  {
    id: 2,
    percentage: 80,
    label: "80% of ocean pollution comes from",
    highlight: "mismanaged plastic waste"
  },
  {
    id: 3,
    percentage: 91,
    label: "91% of plastic ever produced has",
    highlight: "never been recycled"
  }
];
