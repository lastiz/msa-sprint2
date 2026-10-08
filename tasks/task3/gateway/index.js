import { ApolloServer } from '@apollo/server';
import { startStandaloneServer } from '@apollo/server/standalone';
import { ApolloGateway, IntrospectAndCompose, RemoteGraphQLDataSource } from '@apollo/gateway';

class UserDataSource extends RemoteGraphQLDataSource {
  willSendRequest({ request, context }) {
    if (context?.currentUserId) {
      request.http.headers.set('userid', context.currentUserId);
    }
  }
}

const gateway = new ApolloGateway({
  supergraphSdl: new IntrospectAndCompose({
    subgraphs: [
      { name: 'booking', url: process.env.BOOKING_SUBGRAPH_URL ?? 'http://booking-subgraph:4001' },
      { name: 'hotel', url: process.env.HOTEL_SUBGRAPH_URL ?? 'http://hotel-subgraph:4002' },
    ],
  }),
  buildService({ url }) {
    return new UserDataSource({ url });
  },
});

const server = new ApolloServer({ gateway, includeStacktraceInErrorResponses: false });
const { url } = await startStandaloneServer(server, {
  listen: { port: 4000 },
  context: async ({ req }) => ({
    currentUserId: typeof req.headers.userid === 'string' ? req.headers.userid.trim() : undefined,
  }),
});
console.log(`Gateway listening at ${url}`);
