module palette_lut (
    input  logic        clk,
    input  logic [15:0] iter_in,
    input  logic [15:0] max_iter,
    input  logic [7:0]  palette_id,
    output logic [7:0]  rgb_r,
    output logic [7:0]  rgb_g,
    output logic [7:0]  rgb_b
);

    logic [7:0] v8;

    always_comb begin
        // Cheap normalization: use iter_in directly, clamp at max_iter
        if (iter_in >= max_iter)
            v8 = 8'hFF;
        else
            v8 = iter_in[7:0];
    end

    always_comb begin
        case (palette_id)
            8'd0: begin
                // grayscale
                rgb_r = v8;
                rgb_g = v8;
                rgb_b = v8;
            end

            8'd1: begin
                // blue / cyan
                rgb_r = v8 >> 1;
                rgb_g = v8;
                rgb_b = 8'hFF;
            end

            8'd2: begin
                // psychedelic
                rgb_r = v8 ^ 8'h5A;
                rgb_g = ~v8;
                rgb_b = {v8[6:0], 1'b1};
            end

            default: begin
                rgb_r = v8;
                rgb_g = v8;
                rgb_b = v8;
            end
        endcase
    end

endmodule