export const AGE_RANGES = [
  { min: 5, max: 7, key: "5-7" },
  { min: 8, max: 10, key: "8-10" },
  { min: 11, max: 15, key: "11-15" }
];

export function getAgeGroup(age) {
  const group = AGE_RANGES.find(
    (g) => age >= g.min && age <= g.max
  );
  return group ? group.key : null;
}
