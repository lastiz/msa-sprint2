import { ApolloServer } from '@apollo/server';
import { startStandaloneServer } from '@apollo/server/standalone';
import { buildSubgraphSchema } from '@apollo/subgraph';
import gql from 'graphql-tag';

const hotelApiUrl = process.env.HOTEL_API_URL ?? 'http://monolith:8080';

const typeDefs = gql`
  type Hotel @key(fields: "id") {
    id: ID!
    name: String
    city: String
    stars: Int
  }

  type Query {
    hotelsByIds(ids: [ID!]!): [Hotel]
  }
`;

async function fetchHotel(id) {
  const response = await fetch(`${hotelApiUrl}/api/hotels/${encodeURIComponent(id)}`);
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`Hotel API returned HTTP ${response.status}`);
  const hotel = await response.json();
  return {
      ...hotel,
      name: hotel.name ?? hotel.description,
      stars: Math.round(hotel.rating || 0),
  };
}

function createContext() {
  const hotels = new Map();
  return {
    getHotel(id) {
      if (!hotels.has(id)) hotels.set(id, fetchHotel(id));
      return hotels.get(id);
    },
  };
}

const resolvers = {
  Hotel: {
    __resolveReference: ({ id }, { getHotel }) => getHotel(id),
  },
  Query: {
    // Preserve input order and return null at the position of a missing hotel.
    hotelsByIds: (_, { ids }, { getHotel }) => ids.map(id => getHotel(id)),
  },
};

const server = new ApolloServer({
  schema: buildSubgraphSchema([{ typeDefs, resolvers }]),
  includeStacktraceInErrorResponses: false,
});

const { url } = await startStandaloneServer(server, {
  listen: { port: 4002 },
  context: async () => createContext(),
});
console.log(`Hotel subgraph listening at ${url}`);
