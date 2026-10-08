import { ApolloServer } from '@apollo/server';
import { startStandaloneServer } from '@apollo/server/standalone';
import { buildSubgraphSchema } from '@apollo/subgraph';
import grpc from '@grpc/grpc-js';
import protoLoader from '@grpc/proto-loader';
import { GraphQLError } from 'graphql';
import gql from 'graphql-tag';
import { fileURLToPath } from 'node:url';

const protoPath = process.env.BOOKING_PROTO_PATH ?? fileURLToPath(
  new URL('./booking.proto', import.meta.url),
);
const definition = protoLoader.loadSync(protoPath, {
  longs: String,
  defaults: true,
  oneofs: true,
});
const { booking } = grpc.loadPackageDefinition(definition);
const client = new booking.BookingService(
  process.env.BOOKING_GRPC_TARGET ?? 'booking-service:9090',
  grpc.credentials.createInsecure(),
);

const typeDefs = gql`
  type Booking @key(fields: "id") {
    id: ID!
    userId: String!
    hotelId: String!
    promoCode: String
    discountPercent: Int
    hotel: Hotel
  }

  extend type Hotel @key(fields: "id") {
    id: ID! @external
  }

  type Query {
    bookingsByUser(userId: String!): [Booking!]!
  }
`;

function listBookings(userId) {
  return new Promise((resolve, reject) => {
    client.listBookings({ userId }, (error, response) => {
      if (error) {
        console.error('ListBookings failed', { code: error.code });
        reject(error);
        return;
      }
      resolve(response.bookings.filter(item => item.userId === userId));
    });
  });
}

const resolvers = {
  Query: {
    bookingsByUser: async (_, { userId }, { currentUserId }) => {
      if (!currentUserId) {
        throw new GraphQLError('The userid header is required', {
          extensions: { code: 'UNAUTHENTICATED' },
        });
      }
      if (currentUserId !== userId) {
        throw new GraphQLError('Access is denied', {
          extensions: { code: 'FORBIDDEN' },
        });
      }
      return listBookings(userId);
    },
  },
  Booking: {
    hotel: booking => ({ __typename: 'Hotel', id: booking.hotelId })
  }
};

const server = new ApolloServer({
  schema: buildSubgraphSchema([{ typeDefs, resolvers }]),
  includeStacktraceInErrorResponses: false,
});

const { url } = await startStandaloneServer(server, {
  listen: { port: 4001 },
  context: async ({ req }) => ({
    currentUserId: typeof req.headers.userid === 'string' ? req.headers.userid.trim() : undefined,
  }),
});
console.log(`Booking subgraph listening at ${url}`);
