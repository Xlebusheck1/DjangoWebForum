class CentrifugeClient {
    constructor(wsUrl, token) {
        this.wsUrl = wsUrl;
        this.token = token;
        this.client = null;
        this.subscriptions = {};
    }

    connect() {
        this.client = new Centrifuge(this.wsUrl, {
            token: this.token
        });

        this.client.on('connect', function(ctx) {
            console.log('Centrifuge connected', ctx);
        });

        this.client.on('disconnect', function(ctx) {
            console.log('Centrifuge disconnected', ctx);
        });

        this.client.on('error', function(ctx) {
            console.error('Centrifuge error', ctx);
        });

        this.client.connect();
    }

    subscribe(channel, token, handlers) {
        if (this.subscriptions[channel]) {
            return;
        }

        console.log('Subscribing to channel:', channel);
        
        const sub = this.client.newSubscription(channel, {
            token: token
        });

        sub.on('publication', function(ctx) {
            console.log('Publication received on', channel, ctx.data);
            if (handlers.onPublication) {
                handlers.onPublication(ctx.data);
            }
        });

        sub.on('subscribing', function(ctx) {
            console.log(`Subscribing to ${channel}`);
        });

        sub.on('subscribed', function(ctx) {
            console.log(`Subscribed to ${channel}`);
        });

        sub.on('error', function(ctx) {
            console.error(`Subscription error on ${channel}`, ctx);
        });

        sub.subscribe();
        this.subscriptions[channel] = sub;
    }

    disconnect() {
        if (this.client) {
            Object.values(this.subscriptions).forEach(sub => sub.unsubscribe());
            this.client.disconnect();
        }
    }
}