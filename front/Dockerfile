# Use the official nginx image as a parent image
FROM nginx:alpine

# Copy the build output to replace the default nginx contents.
COPY build/ /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Start Nginx and keep it running in the foreground
CMD ["nginx", "-g", "daemon off;"]