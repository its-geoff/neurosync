module coord_gen #(
    parameter SCREEN_W = 640,
    parameter SCREEN_H = 480
)(
    input  logic              clk,
    input  logic              rst_n,

    // pixel inputs from VGA timing
    input  logic [11:0]       px_x,      // assume < 4096
    input  logic [11:0]       px_y,
    input  logic              px_valid,

    // parameters (fixed point Q2.30)
    input  logic signed [31:0] zoom_q30, // scale factor (1.0 = 1<<30)
    input  logic signed [31:0] cx_q30,   // complex center real
    input  logic signed [31:0] cy_q30,   // complex center imag

    // outputs to fractal core (registered)
    output logic              req_valid,
    output logic signed [31:0] c_re_q30,
    output logic signed [31:0] c_im_q30,
    output logic [11:0]      req_px_x,
    output logic [11:0]      req_px_y
);

    // Precompute screen center in pixels
    localparam int CENTER_X = SCREEN_W/2;
    localparam int CENTER_Y = SCREEN_H/2;

    // Convert pixel to normalized coordinates (float): (x - cx)/zoom
    // Using Q2.30: normalized_x = ( (px_x - CENTER_X) * (1.0/zoom) * scale )
    // To avoid divisions, we compute:
    //    dx = px_x - CENTER_X   (integer)
    //    coord_re = cx + dx * (1/zoom) * pixel_scale
    // Choose pixel_scale such that when zoom = 1<<30, one pixel corresponds to e.g. 1/256 units.
    // We'll use PIXEL_UNIT = 1/256 in Q2.30: PIXEL_UNIT_Q30 = (1/256) * (1<<30)
    localparam int PIXEL_UNIT_Q30 = (1<<30) / 256; // Q2.30

    logic signed [31:0] dx_q30, dy_q30;
    logic signed [63:0] tmp_mult;
    
     logic signed [63:0] num_re;
     logic signed [63:0] coord_re64;
     logic signed [63:0] coord_im64;
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            req_valid <= 1'b0;
            c_re_q30 <= 32'sd0;
            c_im_q30 <= 32'sd0;
            req_px_x <= 12'd0;
            req_px_y <= 12'd0;
        end else begin
            if (px_valid) begin
                // dx = px_x - CENTER_X  (signed 16-bit ok)
                int signed dx = $signed({1'b0, px_x}) - CENTER_X;
                int signed dy = $signed({1'b0, px_y}) - CENTER_Y;

                // compute dx_q30 = dx * PIXEL_UNIT_Q30  (Q2.30)
                tmp_mult = dx * PIXEL_UNIT_Q30; // fits 64
                dx_q30 = tmp_mult[31:0];

                tmp_mult = dy * PIXEL_UNIT_Q30;
                dy_q30 = tmp_mult[31:0];

                // scale by inverse zoom: coord_delta = dx_q30 / zoom_q30
                // division by zoom is expensive; compute coord_delta = (dx_q30 * (1<<30)) / zoom_q30
                // So: (dx_q30 << 30) / zoom_q30 -> compute using 64-bit interim
                num_re = $signed({dx_q30, 32'd0}); // dx_q30 << 32 (we'll shift 30)
                // We'll approximate: coord_delta = (dx_q30 * (1<<30)) / zoom_q30
                // Use 64-bit multiply then divide

                if (zoom_q30 != 0) begin
                    coord_re64 = ($signed(dx_q30) <<< 30) / $signed(zoom_q30); // Q2.30
                    coord_im64 = ($signed(dy_q30) <<< 30) / $signed(zoom_q30);
                end else begin
                    coord_re64 = 64'sd0;
                    coord_im64 = 64'sd0;
                end

                // final complex coordinate = center + coord_delta
                c_re_q30 <= $signed(cx_q30) + coord_re64[31:0];
                c_im_q30 <= $signed(cy_q30) + coord_im64[31:0];

                req_px_x <= px_x;
                req_px_y <= px_y;
                req_valid <= 1'b1;
            end else begin
                req_valid <= 1'b0;
            end
        end
    end
endmodule