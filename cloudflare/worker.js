// Cloudflare Worker: /health for the static site (all other routes serve dist/ assets).
export default {
	fetch() {
		return Response.json({ status: 'ok', model_ready: true });
	},
};
